#!/usr/bin/env python3
"""
Deploy all Part 6 Lambda functions to AWS using Terraform.
This script ensures Lambda functions are properly updated by:
1. Optionally packaging the Lambda functions
2. Tainting Lambda resources in Terraform to force recreation
3. Running terraform apply to deploy with the latest code

Usage:
    cd backend
    uv run deploy_all_lambdas.py [--package]
    
Options:
    --package    Force re-packaging of all Lambda functions before deployment
"""

import boto3
import sys
import subprocess
import os
from pathlib import Path
from typing import List, Tuple, Set

from botocore.exceptions import ClientError


def _terraform_state_list(terraform_dir: Path) -> Set[str]:
    """Return addresses in Terraform state (empty set if no state or error)."""
    result = subprocess.run(
        ["terraform", "state", "list"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _run_terraform_import(terraform_dir: Path, address: str, import_id: str) -> bool:
    """Run terraform import; return True on success."""
    result = subprocess.run(
        ["terraform", "import", "-input=false", address, import_id],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"      ✓ Imported {address}")
        return True
    err = (result.stderr or "") + (result.stdout or "")
    if "already managed" in err or "Resource already managed" in err:
        print(f"      ⟳ {address} already in state")
        return True
    print(f"      ⚠️ Import {address}: {err[:300]}")
    return False


def best_effort_import_existing_aws_into_state(terraform_dir: Path) -> None:
    """
    When Terraform state is empty (e.g. GitHub Actions) but resources already exist in AWS
    from a previous run or laptop deploy, import them so apply updates instead of failing
    with EntityAlreadyExists / ResourceConflictException.
    """
    state = _terraform_state_list(terraform_dir)
    reuse = os.environ.get("TF_VAR_reuse_existing_agent_infrastructure", "").lower() in (
        "1",
        "true",
        "yes",
    )

    try:
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
    except ClientError as e:
        print(f"   ⚠️ Skipping import pre-pass (STS): {e}")
        return

    region = (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or os.environ.get("TF_VAR_aws_region")
    )
    if not region:
        session = boto3.Session()
        region = session.region_name or "us-east-1"

    # IAM role + S3 bucket (only when Terraform creates them, not data-source reuse mode)
    if not reuse:
        if "aws_iam_role.lambda_agents_role[0]" not in state:
            iam = boto3.client("iam")
            try:
                iam.get_role(RoleName="alex-lambda-agents-role")
                _run_terraform_import(
                    terraform_dir,
                    "aws_iam_role.lambda_agents_role[0]",
                    "alex-lambda-agents-role",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] != "NoSuchEntity":
                    print(f"   ⚠️ IAM get_role: {e}")

        bucket_name = f"alex-lambda-packages-{account_id}"
        if "aws_s3_bucket.lambda_packages[0]" not in state:
            s3 = boto3.client("s3", region_name=region)
            try:
                s3.head_bucket(Bucket=bucket_name)
                _run_terraform_import(
                    terraform_dir,
                    "aws_s3_bucket.lambda_packages[0]",
                    bucket_name,
                )
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code not in ("404", "NoSuchBucket", "NotFound"):
                    print(f"   ⚠️ S3 head_bucket: {e}")

    # SQS: DLQ first (main queue references DLQ in redrive policy)
    sqs = boto3.client("sqs", region_name=region)
    for resource_addr, queue_name in (
        ("aws_sqs_queue.analysis_jobs_dlq", "alex-analysis-jobs-dlq"),
        ("aws_sqs_queue.analysis_jobs", "alex-analysis-jobs"),
    ):
        if resource_addr in state:
            continue
        try:
            url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
            _run_terraform_import(terraform_dir, resource_addr, url)
        except ClientError as e:
            if e.response["Error"]["Code"] != "AWS.SimpleQueueService.NonExistentQueue":
                print(f"   ⚠️ SQS {queue_name}: {e}")

    # Lambda functions
    lambda_client = boto3.client("lambda", region_name=region)
    for func in ("planner", "tagger", "reporter", "charter", "retirement"):
        addr = f"aws_lambda_function.{func}"
        if addr in state:
            continue
        name = f"alex-{func}"
        try:
            lambda_client.get_function(FunctionName=name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                continue
            print(f"   ⚠️ Lambda get_function {name}: {e}")
            continue
        _run_terraform_import(terraform_dir, addr, name)

    # Refresh state set for downstream taint/apply
    _ = _terraform_state_list(terraform_dir)


def taint_and_deploy_via_terraform() -> bool:
    """
    Deploy Lambda functions using Terraform with forced recreation.
    
    Returns:
        True if successful, False otherwise
    """
    # Change to terraform directory
    terraform_dir = Path(__file__).parent.parent / "terraform" / "6_agents"
    if not terraform_dir.exists():
        print(f"❌ Terraform directory not found: {terraform_dir}")
        return False
    
    # Lambda function names to taint
    lambda_functions = ['planner', 'tagger', 'reporter', 'charter', 'retirement']
    
    print("📌 Step 0: Import existing AWS resources into Terraform state (CI / empty state)...")
    print("-" * 50)
    best_effort_import_existing_aws_into_state(terraform_dir)
    print()

    print("📌 Step 1: Tainting Lambda functions to force recreation...")
    print("-" * 50)
    
    # Taint each Lambda function
    for func in lambda_functions:
        print(f"   Tainting aws_lambda_function.{func}...")
        result = subprocess.run(
            ['terraform', 'taint', f'aws_lambda_function.{func}'],
            cwd=terraform_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 or "already" in result.stderr:
            print(f"      ✓ {func} marked for recreation")
        elif "No such resource instance" in result.stderr:
            print(f"      ⚠️ {func} doesn't exist (will be created)")
        else:
            print(f"      ⚠️ Warning: {result.stderr[:100]}")
    
    print()
    print("🚀 Step 2: Running terraform apply...")
    print("-" * 50)
    
    # Run terraform apply
    result = subprocess.run(
        ['terraform', 'apply', '-auto-approve'],
        cwd=terraform_dir,
        capture_output=False,  # Show output directly
        text=True
    )
    
    if result.returncode == 0:
        print()
        print("✅ Terraform deployment completed successfully!")
        return True
    else:
        print()
        print("❌ Terraform deployment failed!")
        return False

def package_lambda(service_name: str, service_dir: Path) -> bool:
    """
    Package a Lambda function using package_docker.py.
    
    Args:
        service_name: Name of the service (e.g., 'planner')
        service_dir: Path to the service directory
        
    Returns:
        True if successful, False otherwise
    """
    print(f"   📦 Packaging {service_name}...")
    
    package_script = service_dir / 'package_docker.py'
    if not package_script.exists():
        print(f"      ✗ package_docker.py not found in {service_dir}")
        return False
    
    try:
        # Run uv run package_docker.py in the service directory
        result = subprocess.run(
            ['uv', 'run', 'package_docker.py'],
            cwd=service_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Check if zip was created
            zip_path = service_dir / f'{service_name}_lambda.zip'
            if zip_path.exists():
                size_mb = zip_path.stat().st_size / (1024 * 1024)
                print(f"      ✓ Created {size_mb:.1f} MB package")
                return True
            else:
                print(f"      ✗ Package not created")
                return False
        else:
            print(f"      ✗ Packaging failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"      ✗ Error running package_docker.py: {e}")
        return False

def main():
    """Main deployment function."""
    # Check for --package flag
    force_package = '--package' in sys.argv
    
    print("🎯 Deploying Alex Agent Lambda Functions (via Terraform)")
    print("=" * 50)
    
    # Get AWS account ID
    try:
        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        region = boto3.Session().region_name
        print(f"AWS Account: {account_id}")
        print(f"AWS Region: {region}")
    except Exception as e:
        print(f"❌ Failed to get AWS account info: {e}")
        print("   Make sure your AWS credentials are configured")
        sys.exit(1)
    
    print()
    
    # Define Lambda functions to check/package
    backend_dir = Path(__file__).parent
    services = [
        ('planner', backend_dir / 'planner' / 'planner_lambda.zip'),
        ('tagger', backend_dir / 'tagger' / 'tagger_lambda.zip'),
        ('reporter', backend_dir / 'reporter' / 'reporter_lambda.zip'),
        ('charter', backend_dir / 'charter' / 'charter_lambda.zip'),
        ('retirement', backend_dir / 'retirement' / 'retirement_lambda.zip'),
    ]
    
    # Check if packages exist and optionally package them
    print("📋 Checking deployment packages...")
    services_to_package = []
    
    for service_name, zip_path in services:
        service_dir = backend_dir / service_name
        
        if force_package:
            # Force re-packaging all services
            services_to_package.append((service_name, service_dir))
            print(f"   ⟳ {service_name}: Will re-package")
        elif zip_path.exists():
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {service_name}: {size_mb:.1f} MB")
        else:
            print(f"   ✗ {service_name}: Not found")
            services_to_package.append((service_name, service_dir))
    
    # Package missing or all services if requested
    if services_to_package:
        print()
        print("📦 Packaging Lambda functions...")
        failed_packages = []
        
        for service_name, service_dir in services_to_package:
            if not package_lambda(service_name, service_dir):
                failed_packages.append(service_name)
        
        if failed_packages:
            print()
            print(f"❌ Failed to package: {', '.join(failed_packages)}")
            print("   Make sure Docker is running and package_docker.py exists")
            if os.environ.get("CI") == "true":
                sys.exit(1)
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
    
    print()
    
    # Deploy via Terraform with forced recreation
    if taint_and_deploy_via_terraform():
        print()
        print("🎉 All Lambda functions deployed successfully!")
        print()
        print("⚠️  IMPORTANT: Lambda functions were FORCE RECREATED")
        print("   This ensures your latest code is running in AWS")
        print()
        print("Next steps:")
        print("   1. Test locally: cd <service> && uv run test_simple.py")
        print("   2. Run integration test: cd backend && uv run test_full.py")
        print("   3. Monitor CloudWatch Logs for each function")
        sys.exit(0)
    else:
        print()
        print("❌ Deployment failed!")
        print()
        print("💡 Troubleshooting tips:")
        print("   1. Check terraform output for errors")
        print("   2. Ensure all packages exist (use --package flag)")
        print("   3. Verify AWS credentials and permissions")
        print("   4. Check terraform state: cd terraform/6_agents && terraform plan")
        print("   5. CI: ensure GitHub secrets (ALEX_AURORA_*, ALEX_VECTOR_BUCKET, etc.) match your local terraform.tfvars")
        print("   6. MalformedPolicyDocument usually means an empty or wrong ARN — fix secrets, then re-run")
        print("   7. Event source mapping 409: run latest deploy_all_lambdas (imports SQS→planner mapping UUID) or import manually")
        sys.exit(1)

if __name__ == "__main__":
    main()