output "github_actions_role_arn" {
  description = "Set this value as the GitHub Actions secret AWS_ROLE_ARN"
  value       = aws_iam_role.github_actions.arn
}

output "aws_account_id" {
  description = "Current AWS account (sanity check)"
  value       = data.aws_caller_identity.current.account_id
}
