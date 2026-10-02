locals {
  rabbitmq_validation_script = <<-PYTHON
    import json
    import os
    import socket
    import ssl
    import uuid

    import boto3
    import pika


    secret = json.loads(
        boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
        .get_secret_value(SecretId=os.environ["RABBITMQ_SECRET_ARN"])["SecretString"]
    )
    endpoint = secret["host"]
    socket.getaddrinfo(endpoint, secret["port"])
    context = ssl.create_default_context()
    parameters = pika.URLParameters(secret["rabbitmq_url"])
    parameters.ssl_options = pika.SSLOptions(context, endpoint)
    parameters.heartbeat = 30
    parameters.socket_timeout = 10
    parameters.blocked_connection_timeout = 30
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    suffix = uuid.uuid4().hex
    exchange = f"globalchat.validation.{suffix}"
    queue = f"globalchat.validation.{suffix}"
    routing_key = "validation"
    payload = b"globalchat-rabbitmq-validation"

    try:
        channel.confirm_delivery()
        channel.exchange_declare(
            exchange=exchange,
            exchange_type="direct",
            durable=False,
            auto_delete=True,
        )
        channel.queue_declare(queue=queue, durable=False, exclusive=True, auto_delete=True)
        channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
        confirmed = channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=payload,
            properties=pika.BasicProperties(content_type="text/plain", delivery_mode=1),
            mandatory=True,
        )
        if confirmed is False:
            raise RuntimeError("publisher confirmation failed")
        method, _, body = channel.basic_get(queue=queue, auto_ack=False)
        if method is None or body != payload:
            raise RuntimeError("publish/consume verification failed")
        channel.basic_ack(method.delivery_tag)
        channel.queue_delete(queue=queue)
        channel.exchange_delete(exchange=exchange)
    finally:
        if connection.is_open:
            connection.close()

    print("Private DNS, TLS, authentication, AMQP handshake, publish, consume, ACK, and cleanup validation completed.")
  PYTHON
}

resource "random_password" "rabbitmq" {
  length  = 48
  special = false
}

resource "aws_vpc_security_group_ingress_rule" "rabbitmq_from_ecs" {
  security_group_id            = aws_security_group.rabbitmq.id
  description                  = "AMQPS from GlobalChat ECS tasks"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 5671
  ip_protocol                  = "tcp"
  to_port                      = 5671
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_rabbitmq" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "GlobalChat ECS tasks to RabbitMQ over AMQPS"
  referenced_security_group_id = aws_security_group.rabbitmq.id
  from_port                    = 5671
  ip_protocol                  = "tcp"
  to_port                      = 5671
}

resource "aws_mq_broker" "globalchat" {
  broker_name                = "globalchat-production-rabbitmq"
  engine_type                = "RabbitMQ"
  engine_version             = "4.2"
  host_instance_type         = "mq.m7g.medium"
  deployment_mode            = "SINGLE_INSTANCE"
  publicly_accessible        = false
  auto_minor_version_upgrade = true
  apply_immediately          = true
  subnet_ids                 = [aws_subnet.private_data["a"].id]
  security_groups            = [aws_security_group.rabbitmq.id]

  encryption_options {
    use_aws_owned_key = true
  }

  logs {
    general = true
  }

  maintenance_window_start_time {
    day_of_week = "SUNDAY"
    time_of_day = "05:30"
    time_zone   = "UTC"
  }

  user {
    username       = "globalchat_app"
    password       = random_password.rabbitmq.result
    console_access = false
  }

  tags = {
    Name = "globalchat-production-rabbitmq"
  }
}

resource "aws_secretsmanager_secret" "rabbitmq_connection" {
  name                    = "globalchat/production/messaging/rabbitmq"
  description             = "GlobalChat production AMQPS RabbitMQ connection configuration"
  recovery_window_in_days = 30

  tags = {
    Name = "globalchat-production-messaging-rabbitmq"
  }
}

resource "aws_secretsmanager_secret_version" "rabbitmq_connection" {
  secret_id = aws_secretsmanager_secret.rabbitmq_connection.id
  secret_string_wo = jsonencode({
    engine       = "rabbitmq"
    host         = split(":", trimprefix(aws_mq_broker.globalchat.instances[0].endpoints[0], "amqps://"))[0]
    port         = 5671
    username     = "globalchat_app"
    rabbitmq_url = "${replace(aws_mq_broker.globalchat.instances[0].endpoints[0], "amqps://", "amqps://globalchat_app:${random_password.rabbitmq.result}@")}/%2F"
    tls          = true
  })
  secret_string_wo_version = 1
}

data "aws_iam_policy_document" "rabbitmq_validation_assume_role" {
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

resource "aws_iam_role" "rabbitmq_validation" {
  name               = "globalchat-production-rabbitmq-validation"
  description        = "One-off GlobalChat RabbitMQ connectivity validation task role"
  assume_role_policy = data.aws_iam_policy_document.rabbitmq_validation_assume_role.json

  tags = {
    Name = "globalchat-production-rabbitmq-validation"
  }
}

data "aws_iam_policy_document" "rabbitmq_validation" {
  statement {
    sid       = "ReadRabbitMQConnectionSecret"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.rabbitmq_connection.arn]
  }
}

resource "aws_iam_role_policy" "rabbitmq_validation" {
  name   = "globalchat-production-rabbitmq-validation"
  role   = aws_iam_role.rabbitmq_validation.id
  policy = data.aws_iam_policy_document.rabbitmq_validation.json
}

resource "aws_cloudwatch_log_group" "rabbitmq_validation" {
  name              = "/globalchat/production/rabbitmq-validation"
  retention_in_days = 7

  tags = {
    Name = "globalchat-production-rabbitmq-validation-logs"
  }
}

resource "aws_ecs_task_definition" "rabbitmq_validation" {
  family                   = "globalchat-production-rabbitmq-validation"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.rabbitmq_validation.arn

  container_definitions = jsonencode([
    {
      name       = "rabbitmq-validation"
      image      = "public.ecr.aws/docker/library/python:3.12-slim"
      essential  = true
      entryPoint = ["/bin/sh", "-c"]
      command = [
        "pip install --quiet 'boto3>=1.35,<2' 'pika>=1.3,<2' && echo \"$VALIDATION_SCRIPT_B64\" | base64 -d > /tmp/validate.py && python /tmp/validate.py",
      ]
      environment = [
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "RABBITMQ_SECRET_ARN"
          value = aws_secretsmanager_secret.rabbitmq_connection.arn
        },
        {
          name  = "VALIDATION_SCRIPT_B64"
          value = base64encode(local.rabbitmq_validation_script)
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.rabbitmq_validation.name
          "awslogs-region"        = "ap-south-1"
          "awslogs-stream-prefix" = "validation"
        }
      }
    },
  ])

  depends_on = [aws_secretsmanager_secret_version.rabbitmq_connection]

  tags = {
    Name = "globalchat-production-rabbitmq-validation"
  }
}

data "aws_iam_policy_document" "github_rabbitmq_foundation" {
  statement {
    sid = "ManageGlobalChatRabbitMQ"
    actions = [
      "mq:CreateBroker",
      "mq:CreateTags",
      "mq:DeleteBroker",
      "mq:DeleteTags",
      "mq:DescribeBroker",
      "mq:ListTags",
      "mq:RebootBroker",
      "mq:UpdateBroker",
    ]
    resources = ["arn:aws:mq:ap-south-1:${local.account_id}:broker:globalchat-production-rabbitmq:*"]
  }

  statement {
    sid       = "DiscoverRabbitMQOptions"
    actions   = ["mq:DescribeBrokerEngineTypes", "mq:DescribeBrokerInstanceOptions"]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatRabbitMQSecret"
    actions = [
      "secretsmanager:CreateSecret",
      "secretsmanager:DeleteSecret",
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:ListSecretVersionIds",
      "secretsmanager:PutResourcePolicy",
      "secretsmanager:RestoreSecret",
      "secretsmanager:TagResource",
      "secretsmanager:UntagResource",
      "secretsmanager:UpdateSecret",
      "secretsmanager:UpdateSecretVersionStage",
    ]
    resources = ["arn:aws:secretsmanager:ap-south-1:${local.account_id}:secret:globalchat/production/messaging/*"]
  }

  statement {
    sid = "ManageRabbitMQValidationRole"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DeleteRolePolicy",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRolePolicies",
      "iam:ListRoleTags",
      "iam:PassRole",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRoleDescription",
    ]
    resources = ["arn:aws:iam::${local.account_id}:role/globalchat-production-rabbitmq-validation"]
  }

  statement {
    sid = "ManageRabbitMQValidationTaskDefinition"
    actions = [
      "ecs:DeregisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:TagResource",
      "ecs:UntagResource",
    ]
    resources = ["*"]
  }

  statement {
    sid = "ManageRabbitMQNetworkRules"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = [
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.ecs.id}",
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.rabbitmq.id}",
    ]
  }

  statement {
    sid       = "DiscoverRabbitMQNetwork"
    actions   = ["ec2:DescribeSecurityGroupRules", "ec2:DescribeSecurityGroups"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "github_rabbitmq_foundation" {
  name        = "globalchat-production-rabbitmq-foundation"
  description = "Least-privilege GitHub deployment permissions for the GlobalChat RabbitMQ foundation"
  policy      = data.aws_iam_policy_document.github_rabbitmq_foundation.json

  tags = {
    Name = "globalchat-production-rabbitmq-foundation"
  }
}

resource "aws_iam_role_policy_attachment" "github_rabbitmq_foundation" {
  role       = aws_iam_role.github_deploy.name
  policy_arn = aws_iam_policy.github_rabbitmq_foundation.arn
}
