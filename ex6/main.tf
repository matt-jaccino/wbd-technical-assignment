terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.15.0, < 6.0.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda_role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"]
}

data "aws_iam_policy_document" "s3_access" {
  statement {
    sid = "S3Read"
    effect = "Allow"
    actions = [
      "s3:GetBucketPublicAccessBlock",
      "s3:ListAllMyBuckets"
    ]
    resources = ["*"]
  }
  statement {
    sid = "S3BlockPublic"
    effect = "Allow"
    actions = [
      "s3:PutBucketPublicAccessBlock"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "s3_access_policy" {
  name = "s3_access"
  role = aws_iam_role.lambda_role.id

  policy = data.aws_iam_policy_document.s3_access.json
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "lambda.py"
  output_path = "lambda_code.zip"
}

resource "aws_lambda_function" "bucket_lockdown" {
  filename      = "lambda_function_payload.zip"
  function_name = "lambda_function_name"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda.lambda_handler"

  source_code_hash = data.archive_file.lambda.output_base64sha256

  vpc_config {
    subnet_ids = ["subnet-1234", "subnet-2345"]
    security_group_ids = ["sg-12345"]
  }

  runtime = "python3.12"
}

resource "aws_lambda_permission" "bucket_lockdown_perm" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bucket_lockdown.arn
  principal     = "config.amazonaws.com"
  statement_id  = "AllowExecutionFromConfig"
}

resource "aws_config_config_rule" "bucket_lockdown_rule" {
  name = "bucket_lockdown_rule"

  input_parameters = jsonencode({"tag": jsonencode({"access": "public"})})

  scope {
    compliance_resource_types = ["AWS::S3::Bucket"]
  }

  source {
    owner             = "CUSTOM_LAMBDA"
    source_identifier = aws_lambda_function.bucket_lockdown.arn
  }

  depends_on = [
    aws_lambda_permission.bucket_lockdown_perm
  ]
}
