locals {
  backend_services = toset([
    "organization",
    "identity",
    "user",
    "conversation",
    "messaging",
    "realtime",
    "media",
    "notification",
    "gateway",
  ])

  ecr_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expire untagged images after 14 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 14
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep the 30 most recent images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      },
    ]
  })
}

resource "aws_ecr_repository" "backend" {
  for_each = local.backend_services

  name                 = "globalchat/${each.key}"
  image_tag_mutability = "IMMUTABLE"

  encryption_configuration {
    encryption_type = "AES256"
  }

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "globalchat-${each.key}"
    Service = each.key
  }
}

resource "aws_ecr_lifecycle_policy" "backend" {
  for_each = aws_ecr_repository.backend

  repository = each.value.name
  policy     = local.ecr_lifecycle_policy
}

resource "aws_ecs_cluster" "globalchat" {
  name = "globalchat-production"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = {
    Name = "globalchat-production"
  }
}

resource "aws_ecs_cluster_capacity_providers" "globalchat" {
  cluster_name = aws_ecs_cluster.globalchat.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    base              = 1
    weight            = 1
  }
}

resource "aws_service_discovery_private_dns_namespace" "globalchat" {
  name        = "globalchat.internal"
  description = "GlobalChat production private service discovery namespace"
  vpc         = aws_vpc.globalchat.id

  tags = {
    Name = "globalchat-production-private-namespace"
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  for_each = local.backend_services

  name              = "/globalchat/production/${each.key}"
  retention_in_days = 30

  tags = {
    Name    = "globalchat-production-${each.key}-logs"
    Service = each.key
  }
}

data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    sid     = "EcsTasksAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name                 = "globalchat-production-ecs-task-execution"
  description          = "GlobalChat production ECS task execution role"
  assume_role_policy   = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
  max_session_duration = 3600

  tags = {
    Name = "globalchat-production-ecs-task-execution"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "github_container_foundation" {
  statement {
    sid = "ManageGlobalChatEcrRepositories"
    actions = [
      "ecr:CreateRepository",
      "ecr:DeleteLifecyclePolicy",
      "ecr:DeleteRepository",
      "ecr:DescribeRepositories",
      "ecr:GetLifecyclePolicy",
      "ecr:ListTagsForResource",
      "ecr:PutImageScanningConfiguration",
      "ecr:PutImageTagMutability",
      "ecr:PutLifecyclePolicy",
      "ecr:TagResource",
      "ecr:UntagResource",
    ]
    resources = ["arn:aws:ecr:ap-south-1:${local.account_id}:repository/globalchat/*"]
  }

  statement {
    sid = "DiscoverGlobalChatEcrRepositories"
    actions = [
      "ecr:DescribeRepositories",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatEcsCluster"
    actions = [
      "ecs:CreateCluster",
      "ecs:DeleteCluster",
      "ecs:DeregisterContainerInstance",
      "ecs:DescribeClusters",
      "ecs:ListAttributes",
      "ecs:ListContainerInstances",
      "ecs:ListServices",
      "ecs:ListTagsForResource",
      "ecs:PutClusterCapacityProviders",
      "ecs:TagResource",
      "ecs:UntagResource",
      "ecs:UpdateCluster",
      "ecs:UpdateClusterSettings",
    ]
    resources = ["arn:aws:ecs:ap-south-1:${local.account_id}:cluster/globalchat-production"]
  }

  statement {
    sid = "ManageGlobalChatServiceDiscoveryNamespace"
    actions = [
      "servicediscovery:CreatePrivateDnsNamespace",
      "servicediscovery:DeleteNamespace",
      "servicediscovery:GetNamespace",
      "servicediscovery:ListTagsForResource",
      "servicediscovery:TagResource",
      "servicediscovery:UntagResource",
      "servicediscovery:UpdatePrivateDnsNamespace",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatLogGroups"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:ListTagsForResource",
      "logs:PutRetentionPolicy",
      "logs:TagResource",
      "logs:UntagResource",
    ]
    resources = [
      "arn:aws:logs:ap-south-1:${local.account_id}:log-group:/globalchat/production/*",
    ]
  }

  statement {
    sid       = "DiscoverGlobalChatLogGroups"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatExecutionRole"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DetachRolePolicy",
      "iam:GetRole",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRolePolicies",
      "iam:ListRoleTags",
      "iam:PassRole",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRoleDescription",
    ]
    resources = [
      "arn:aws:iam::${local.account_id}:role/globalchat-production-ecs-task-execution",
    ]
  }
}

resource "aws_iam_role_policy" "github_container_foundation" {
  name   = "globalchat-production-container-foundation"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_container_foundation.json
}
