variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "aurora_cluster_arn" {
  description = "ARN of the Aurora cluster from Part 5"
  type        = string
}

variable "aurora_secret_arn" {
  description = "ARN of the Secrets Manager secret from Part 5"
  type        = string
}

variable "vector_bucket" {
  description = "S3 Vectors bucket name from Part 3"
  type        = string
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for Lambda agents (https://openrouter.ai)"
  type        = string
  sensitive   = true
}

variable "openrouter_model" {
  description = "OpenRouter model slug, e.g. openai/gpt-4o-mini"
  type        = string
  default     = "openai/gpt-4o-mini"
}

variable "openrouter_base_url" {
  description = "OpenRouter OpenAI-compatible API base URL"
  type        = string
  default     = "https://openrouter.ai/api/v1"
}

variable "sagemaker_endpoint" {
  description = "SageMaker endpoint name from Part 2"
  type        = string
  default     = "alex-embedding-endpoint"
}

variable "polygon_api_key" {
  description = "Polygon.io API key for market data"
  type        = string
}

variable "polygon_plan" {
  description = "Polygon.io plan type (free or paid)"
  type        = string
  default     = "free"
}

# LangFuse observability variables (optional)
variable "langfuse_public_key" {
  description = "LangFuse public key for observability (optional)"
  type        = string
  default     = ""
  sensitive   = false
}

variable "langfuse_secret_key" {
  description = "LangFuse secret key for observability (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "langfuse_host" {
  description = "LangFuse host URL (optional)"
  type        = string
  default     = "https://us.cloud.langfuse.com"
}

# Optional: enable OpenAI Agents SDK trace export (only if not using OpenRouter)
variable "openai_api_key" {
  description = "OpenAI API key for Agents SDK tracing (optional; unused when OPENROUTER_API_KEY is set in Lambda)"
  type        = string
  default     = ""
  sensitive   = true
}