variable "production_image_digests" {
  description = "Immutable manifest-list digests for the production source commit fe839197a8fc."
  type        = map(string)
  default = {
    organization = "sha256:c4f9e9ca84aeb86d8189197e523486bb5f6a04b606e0f4c2182f338d031000be"
    identity     = "sha256:1dae2f8b53b3703ab833028d879a6866e81c57bc9b6bea86306792389c8c1028"
    user         = "sha256:098a250f6febeed985ae8afac50c2a01d941efe4d98f0f6d15d4d21b49cd30d2"
    conversation = "sha256:c5edd6ba860f67a750e76fbfe75ea0adb523109d9a752c5fceb43d9929d400f5"
    messaging    = "sha256:0159e7739740f3def20e9bf60669e3c4be10ef79d858325daf6af5d2f8007442"
    realtime     = "sha256:355163c06c7a267c64abdd57d85e90303919c1fe3b0cbd9872901c238fd55789"
    media        = "sha256:3485c018a724aba930c1540b091528bbee950ccab0ef6930fe97cb822bd25669"
    notification = "sha256:da524b5b8aa3c97cc5664276843e0df8033667542236f47b7c3fba089eac8e05"
    gateway      = "sha256:cea7032cb3b29423c58469740f0cd88e470391919ce397f58a2bf8059c988b1a"
  }
}

locals {
  step10a_images = {
    for service, repository in aws_ecr_repository.backend :
    service => "${repository.repository_url}@${var.production_image_digests[service]}"
  }

  cloud_map_apis = {
    for key, process in local.deployment_processes :
    process.service => process if process.cloud_map && process.service != "realtime"
  }

  migration_commands = merge(
    { organization = ["python", "manage.py", "migrate", "--noinput"] },
    {
      for service in ["identity", "user", "conversation", "messaging", "media", "notification"] :
      service => ["alembic", "upgrade", "head"]
    },
  )

  media_s3_processes = toset(["media-api", "media-consumer"])
}

resource "aws_service_discovery_service" "api" {
  for_each = local.cloud_map_apis

  name = each.key

  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.globalchat.id
    routing_policy = "MULTIVALUE"

    dns_records {
      ttl  = 10
      type = "A"
    }
  }

  tags = {
    Name    = "globalchat-production-${each.key}-discovery"
    Service = each.key
  }
}

resource "aws_ecs_task_definition" "process" {
  for_each = local.deployment_processes

  family                   = "globalchat-production-${each.key}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = contains(local.media_s3_processes, each.key) ? aws_iam_role.media_task.arn : null

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name        = each.key
    image       = local.step10a_images[each.value.service]
    essential   = true
    command     = split(" ", each.value.command)
    stopTimeout = 60
    environment = [for name, value in each.value.environment : { name = name, value = value }]
    secrets = [
      for name, value_from in each.value.secrets :
      { name = name, valueFrom = value_from }
      if !(
        each.value.service == "notification" &&
        contains(["consumer", "outbox"], each.value.name) &&
        name == "FIREBASE_CREDENTIALS_JSON"
      )
    ]
    portMappings = each.value.port == null ? [] : [{ containerPort = each.value.port, protocol = "tcp" }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend[each.value.service].name
        "awslogs-region"        = "ap-south-1"
        "awslogs-stream-prefix" = each.key
      }
    }
  }])

  depends_on = [aws_cloudwatch_log_group.backend]

  tags = {
    Name    = "globalchat-production-${each.key}"
    Service = each.value.service
    Process = each.value.name
  }
}

resource "aws_ecs_task_definition" "migration" {
  for_each = local.migration_commands

  family                   = "globalchat-production-${each.key}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([{
    name        = "${each.key}-migration"
    image       = local.step10a_images[each.key]
    essential   = true
    command     = each.value
    stopTimeout = 60
    environment = [
      for name, value in local.service_configuration[each.key].environment :
      { name = name, value = value }
    ]
    secrets = [
      for name, value_from in local.service_configuration[each.key].secrets :
      { name = name, valueFrom = value_from }
      if !(each.key == "notification" && name == "FIREBASE_CREDENTIALS_JSON")
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend[each.key].name
        "awslogs-region"        = "ap-south-1"
        "awslogs-stream-prefix" = "${each.key}-migration"
      }
    }
  }])

  depends_on = [aws_cloudwatch_log_group.backend]

  tags = {
    Name    = "globalchat-production-${each.key}-migration"
    Service = each.key
    Process = "migration"
  }
}

resource "aws_lb_target_group" "gateway" {
  name        = "globalchat-production-gateway"
  port        = 8008
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.globalchat.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health/ready"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = {
    Name    = "globalchat-production-gateway"
    Service = "gateway"
  }
}

resource "aws_vpc_security_group_egress_rule" "alb_to_gateway" {
  security_group_id            = aws_security_group.alb.id
  description                  = "ALB to future Gateway targets"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8008
  ip_protocol                  = "tcp"
  to_port                      = 8008
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_gateway" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Gateway traffic from GlobalChat ALB"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8008
  ip_protocol                  = "tcp"
  to_port                      = 8008
}

resource "aws_vpc_security_group_ingress_rule" "ecs_internal_http" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Gateway and internal API traffic between GlobalChat ECS tasks"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8000
  ip_protocol                  = "tcp"
  to_port                      = 8006
}

resource "aws_vpc_security_group_egress_rule" "ecs_internal_http" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "Gateway and internal API traffic between GlobalChat ECS tasks"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 8000
  ip_protocol                  = "tcp"
  to_port                      = 8006
}

data "aws_iam_policy_document" "github_step10a_ecs" {
  statement {
    sid = "ManageGlobalChatProcessTaskDefinitions"
    actions = [
      "ecs:DeregisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
      "ecs:RegisterTaskDefinition",
      "ecs:TagResource",
      "ecs:UntagResource",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatDiscoveryServices"
    actions = [
      "servicediscovery:CreateService",
      "servicediscovery:DeleteService",
      "servicediscovery:GetService",
      "servicediscovery:ListServices",
      "servicediscovery:ListTagsForResource",
      "servicediscovery:TagResource",
      "servicediscovery:UntagResource",
      "servicediscovery:UpdateService",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatGatewayTargetGroup"
    actions = [
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:CreateTargetGroup",
      "elasticloadbalancing:DeleteTargetGroup",
      "elasticloadbalancing:DescribeTargetGroups",
      "elasticloadbalancing:DescribeTargetHealth",
      "elasticloadbalancing:ModifyTargetGroup",
      "elasticloadbalancing:ModifyTargetGroupAttributes",
      "elasticloadbalancing:RemoveTags",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatGatewaySecurityGroupRules"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:DescribeSecurityGroupRules",
      "ec2:DescribeSecurityGroups",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_step10a_ecs" {
  name   = "globalchat-production-step10a-ecs"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_step10a_ecs.json
}
