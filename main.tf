terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "paguebem-terraform-state"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
    # key é passado via -backend-config="key=..." no terraform init
    # Dev:  lambda/dev/terraform.tfstate
    # Prod: lambda/prod/terraform.tfstate
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
      Repository  = "PagueBem-terraform-lambda"
    }
  }
}

# =============================================================================
# ECR Repository
# =============================================================================
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }
}

# =============================================================================
# Docker Build & Push
# =============================================================================
resource "null_resource" "docker_build_push" {
  triggers = {
    dockerfile_hash   = filemd5("${path.module}/lambda/Dockerfile")
    main_hash         = filemd5("${path.module}/lambda/main.py")
    requirements_hash = filemd5("${path.module}/lambda/requirements.txt")
    always_run        = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = <<-EOT
      $ErrorActionPreference = 'Stop'
      $registry = "${aws_ecr_repository.api.repository_url}" -split '/' | Select-Object -First 1
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin $registry
      docker build --platform linux/amd64 --provenance=false -t ${var.project_name}-api:latest "${path.module}/lambda"
      docker tag ${var.project_name}-api:latest "${aws_ecr_repository.api.repository_url}:latest"
      docker push "${aws_ecr_repository.api.repository_url}:latest"
    EOT
  }

  depends_on = [aws_ecr_repository.api]
}

# =============================================================================
# IAM Role for Lambda
# =============================================================================
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-api-${var.environment}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-api-${var.environment}-role"
  }
}

# CloudWatch Logs policy
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB access policy
resource "aws_iam_policy" "lambda_dynamodb" {
  name        = "${var.project_name}-api-${var.environment}-dynamodb"
  description = "Allow Lambda to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = var.dynamodb_table_arns
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamodb.arn
}

# =============================================================================
# CloudWatch Log Group
# =============================================================================
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-api-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-api-${var.environment}-logs"
  }
}

# =============================================================================
# Lambda Function
# =============================================================================
resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:latest"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = merge(
      {
        ENVIRONMENT            = var.environment
        USUARIOS_TABLE_NAME    = var.usuarios_table_name
        PRODUTOS_TABLE_NAME    = var.produtos_table_name
      },
      var.extra_env_vars
    )
  }

  depends_on = [
    null_resource.docker_build_push,
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_logs,
    aws_iam_role_policy_attachment.lambda_dynamodb
  ]

  tags = {
    Name = "${var.project_name}-api-${var.environment}"
  }
}
