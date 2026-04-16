#!/usr/bin/env bash
# Twin-style teardown: delete all AWS resources managed by Alex Terraform stacks (local state per stack).
# Usage: ./scripts/destroy.sh <environment> --yes
#   environment — label for logs (e.g. demo); must match GitHub Actions "confirm" workflow pattern.
#   --yes       — required so accidental runs are harder (CI passes this after human confirmation).
#
# OpenRouter keys are external; revoke them at https://openrouter.ai after Lambdas are gone.
set -euo pipefail

usage() {
  echo "Usage: $0 <environment> --yes"
  echo "  Destroys Terraform stacks in reverse dependency order (8_enterprise → … → 2_sagemaker)."
  echo "  Run from the same machine that ran terraform apply (local terraform.tfstate in each stack),"
  echo "  or configure an S3 backend in each stack so CI runners can see state."
  exit 1
}

if [[ $# -ne 2 ]] || [[ "$2" != "--yes" ]]; then
  usage
fi

ENVIRONMENT="$1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALEX_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TF_ROOT="${ALEX_ROOT}/terraform"

# Reverse of deploy order: consumers first, then shared services, then foundation (see terraform/README.md).
STACKS=(
  "8_enterprise"
  "7_frontend"
  "6_agents"
  "4_researcher"
  "3_ingestion"
  "5_database"
  "2_sagemaker"
)

echo "============================================================"
echo "Alex Terraform destroy — environment: ${ENVIRONMENT}"
echo "Terraform root: ${TF_ROOT}"
echo "============================================================"

for stack in "${STACKS[@]}"; do
  dir="${TF_ROOT}/${stack}"
  if [[ ! -d "${dir}" ]]; then
    echo "[skip] ${stack}: directory missing"
    continue
  fi
  if [[ ! -f "${dir}/main.tf" ]]; then
    echo "[skip] ${stack}: no main.tf"
    continue
  fi

  echo ""
  echo "---- Destroying stack: ${stack} ----"
  (cd "${dir}" && terraform init -input=false && terraform destroy -auto-approve)
done

echo ""
echo "✅ Destroy sequence finished for '${ENVIRONMENT}'."
echo "   Confirm in AWS Console that resources are gone; revoke OpenRouter keys if you no longer need them."
