variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for the researcher agent (https://openrouter.ai)"
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

variable "alex_api_endpoint" {
  description = "Alex API endpoint from Part 3"
  type        = string
}

variable "alex_api_key" {
  description = "Alex API key from Part 3"
  type        = string
  sensitive   = true
}

variable "scheduler_enabled" {
  description = "Enable automated research scheduler"
  type        = bool
  default     = false
}