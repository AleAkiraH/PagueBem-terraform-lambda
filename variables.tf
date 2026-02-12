variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "paguebem"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}

# --- DynamoDB references (from dynamodb outputs) ---

variable "usuarios_table_name" {
  description = "Name of the Usuarios DynamoDB table"
  type        = string
}

variable "usuarios_table_arn" {
  description = "ARN of the Usuarios DynamoDB table"
  type        = string
}

variable "qrcode_itens_table_name" {
  description = "Name of the QrCodeItens DynamoDB table"
  type        = string
}

variable "qrcode_itens_table_arn" {
  description = "ARN of the QrCodeItens DynamoDB table"
  type        = string
}

variable "dynamodb_table_arns" {
  description = "List of all DynamoDB table ARNs the Lambda needs access to (include index ARNs)"
  type        = list(string)
}

variable "extra_env_vars" {
  description = "Additional environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}
