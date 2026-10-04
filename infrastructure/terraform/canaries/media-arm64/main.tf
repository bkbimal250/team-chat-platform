terraform {
  required_version = ">= 1.10.0, < 2.0.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  # Separate state prevents this preparation from including pending release images.
  backend "s3" {
    bucket       = "globalchat-production-terraform-state-167667034490-ap-south-1"
    key          = "production/canaries/media-arm64.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = "ap-south-1"
  default_tags {
    tags = { Project = "GlobalChat", Environment = "production", ManagedBy = "Terraform" }
  }
}

variable "arm64_image" {
  description = "Verified ARM64 manifest digest in the existing Media ECR repository. Publication is a separate approval gate."
  type        = string
  validation {
    condition     = can(regex("^167667034490\\.dkr\\.ecr\\.ap-south-1\\.amazonaws\\.com/globalchat/media@sha256:[0-9a-f]{64}$", var.arm64_image))
    error_message = "Use an immutable digest in the existing production Media repository."
  }
}

data "aws_ecs_task_definition" "baseline" {
  # Pinned production x86 definition, not latest or the pending feature release.
  task_definition = "arn:aws:ecs:ap-south-1:167667034490:task-definition/globalchat-production-media-api:1"
}

locals {
  baseline_containers = jsondecode(data.aws_ecs_task_definition.baseline.container_definitions)
  containers = [for container in local.baseline_containers : merge(container, {
    image = var.arm64_image
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8005/health/ready', timeout=3)\""]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
    logConfiguration = merge(container.logConfiguration, {
      options = merge(container.logConfiguration.options, {
        "awslogs-stream-prefix" = "media-arm64-canary"
      })
    })
  })]
}

# Definition plus paused service: no running task, Cloud Map registration or ALB target.
resource "aws_ecs_task_definition" "canary" {
  family                   = "globalchat-production-media-arm64-canary"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.aws_ecs_task_definition.baseline.execution_role_arn
  task_role_arn            = data.aws_ecs_task_definition.baseline.task_role_arn
  container_definitions    = jsonencode(local.containers)
  skip_destroy             = true

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  lifecycle {
    precondition {
      condition     = length(local.baseline_containers) == 1 && local.baseline_containers[0].name == "media-api"
      error_message = "Baseline must remain the reviewed single-container Media API definition."
    }
    precondition {
      condition     = local.baseline_containers[0].image == "167667034490.dkr.ecr.ap-south-1.amazonaws.com/globalchat/media@sha256:3485c018a724aba930c1540b091528bbee950ccab0ef6930fe97cb822bd25669"
      error_message = "Production baseline changed: recapture rollback evidence before proceeding."
    }
  }
  tags = { Name = "globalchat-production-media-arm64-canary", Service = "media", Process = "api", Purpose = "arm64-canary" }
}

# A service supplies standard CPU/MemoryUtilization without paid Container Insights.
# Starting even one task requires a separate reviewed change and approval.
resource "aws_ecs_service" "canary" {
  name                               = "globalchat-production-media-arm64-canary"
  cluster                            = "arn:aws:ecs:ap-south-1:167667034490:cluster/globalchat-production"
  task_definition                    = aws_ecs_task_definition.canary.arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = 0
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  enable_ecs_managed_tags            = true
  propagate_tags                     = "SERVICE"

  network_configuration {
    # Captured from the deployed Media service; no new networking resources.
    subnets          = ["subnet-02568a1d641f95a13", "subnet-0635dc58e163f26f0"]
    security_groups  = ["sg-0e85a60a11fd722e0"]
    assign_public_ip = false
  }
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  tags = { Name = "globalchat-production-media-arm64-canary", Service = "media", Process = "api", Purpose = "arm64-canary" }
}

output "rollback_task_definition" {
  value = data.aws_ecs_task_definition.baseline.arn
}

output "rollback_image" {
  value = local.baseline_containers[0].image
}
