variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "tf_state_bucket" {
  description = "S3 bucket containing shared Terraform states for other parts"
  type        = string
}

variable "tf_state_region" {
  description = "AWS region for shared Terraform state bucket"
  type        = string
  default     = "us-east-1"
}

variable "tf_state_database_key" {
  description = "State object key for Part 5 database"
  type        = string
  default     = "alex/5_database/terraform.tfstate"
}

variable "tf_state_agents_key" {
  description = "State object key for Part 6 agents"
  type        = string
  default     = "alex/6_agents/terraform.tfstate"
}

# Clerk validation happens in Lambda, not at API Gateway level
variable "clerk_jwks_url" {
  description = "Clerk JWKS URL for JWT validation in Lambda"
  type        = string
}

variable "clerk_issuer" {
  description = "Clerk issuer URL (kept for Lambda environment)"
  type        = string
  default     = ""  # Not actually used but kept for backwards compatibility
}