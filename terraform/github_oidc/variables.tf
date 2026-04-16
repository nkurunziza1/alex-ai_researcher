variable "aws_region" {
  description = "AWS region (e.g. us-east-1)"
  type        = string
  default     = "us-east-1"
}

variable "github_repository" {
  description = "GitHub repository allowed to assume this role — format owner/repo only (no https://)"
  type        = string
}

variable "role_name" {
  description = "IAM role name for GitHub Actions OIDC"
  type        = string
  default     = "github-actions-alex-deploy"
}

variable "create_github_oidc_provider" {
  description = "Set true only if this AWS account does NOT already have the GitHub OIDC provider (token.actions.githubusercontent.com). If you get 409 EntityAlreadyExists, leave false."
  type        = bool
  default     = false
}
