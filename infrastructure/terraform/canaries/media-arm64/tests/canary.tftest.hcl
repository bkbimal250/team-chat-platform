mock_provider "aws" {
  mock_data "aws_ecs_task_definition" {
    defaults = {
      arn                = "arn:aws:ecs:ap-south-1:167667034490:task-definition/globalchat-production-media-api:1"
      execution_role_arn = "arn:aws:iam::167667034490:role/globalchat-production-ecs-task-execution"
      task_role_arn      = "arn:aws:iam::167667034490:role/globalchat-production-media-task"
      container_definitions = jsonencode([{
        name         = "media-api"
        image        = "167667034490.dkr.ecr.ap-south-1.amazonaws.com/globalchat/media@sha256:3485c018a724aba930c1540b091528bbee950ccab0ef6930fe97cb822bd25669"
        command      = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
        essential    = true
        secrets      = [{ name = "DATABASE_URL", valueFrom = "arn:aws:secretsmanager:ap-south-1:167667034490:secret:fixture-database:database_url::" }]
        environment  = [{ name = "APP_ENV", value = "production" }]
        portMappings = [{ containerPort = 8005, protocol = "tcp" }]
        logConfiguration = {
          logDriver = "awslogs"
          options   = { "awslogs-group" = "/globalchat/production/media", "awslogs-region" = "ap-south-1", "awslogs-stream-prefix" = "media-api" }
        }
      }])
    }
  }
}

variables {
  arm64_image = "167667034490.dkr.ecr.ap-south-1.amazonaws.com/globalchat/media@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}

run "isolated_arm64_definition" {
  command = plan
  assert {
    condition     = aws_ecs_task_definition.canary.cpu == "256" && aws_ecs_task_definition.canary.memory == "512" && aws_ecs_task_definition.canary.runtime_platform[0].cpu_architecture == "ARM64"
    error_message = "Only the reviewed Media ARM64 size is permitted."
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.canary.container_definitions)[0].secrets == local.baseline_containers[0].secrets && jsondecode(aws_ecs_task_definition.canary.container_definitions)[0].command == local.baseline_containers[0].command && jsondecode(aws_ecs_task_definition.canary.container_definitions)[0].environment == local.baseline_containers[0].environment
    error_message = "Canary must preserve baseline secrets references, command and environment."
  }
  assert {
    condition     = output.rollback_image == local.baseline_containers[0].image && output.rollback_task_definition == data.aws_ecs_task_definition.baseline.arn
    error_message = "Immutable x86 rollback references must remain intact."
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.canary.container_definitions)[0].healthCheck.startPeriod == 60 && jsondecode(aws_ecs_task_definition.canary.container_definitions)[0].logConfiguration.options["awslogs-stream-prefix"] == "media-arm64-canary"
    error_message = "Readiness checks and separate log prefix are required."
  }
  assert {
    condition     = aws_ecs_service.canary.desired_count == 0 && !aws_ecs_service.canary.network_configuration[0].assign_public_ip && length(aws_ecs_service.canary.load_balancer) == 0 && length(aws_ecs_service.canary.service_registries) == 0
    error_message = "Preparation must not run tasks, expose public IPs, or register public/Cloud Map traffic."
  }
}
