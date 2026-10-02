locals {
  cache_validation_script = <<-PYTHON
    import json
    import os
    import time
    import uuid

    import boto3
    import redis


    secret = json.loads(
        boto3.client("secretsmanager", region_name=os.environ["AWS_REGION"])
        .get_secret_value(SecretId=os.environ["REDIS_SECRET_ARN"])["SecretString"]
    )
    client = redis.Redis.from_url(secret["redis_url_db0"], decode_responses=True)
    conversation_client = redis.Redis.from_url(secret["redis_url_db1"], decode_responses=True)
    prefix = f"globalchat:validation:{uuid.uuid4()}"
    value_key = f"{prefix}:value"
    metadata_key = f"{prefix}:metadata"
    presence_key = f"{prefix}:presence"
    dedup_key = f"{prefix}:dedup"
    conversation_key = f"{prefix}:conversation"
    channel = f"{prefix}:channel"

    try:
        if not client.ping() or not conversation_client.ping():
            raise RuntimeError("authenticated TLS PING failed")
        if not client.set(value_key, "ok", ex=30) or client.get(value_key) != "ok":
            raise RuntimeError("SET/GET failed")
        ttl = client.ttl(value_key)
        if ttl <= 0 or ttl > 30:
            raise RuntimeError("TTL verification failed")
        client.hset(metadata_key, mapping={"instance_id": "validation", "state": "connected"})
        client.expire(metadata_key, 30)
        if client.hget(metadata_key, "state") != "connected":
            raise RuntimeError("metadata semantics failed")
        if not client.set(presence_key, "online", ex=30):
            raise RuntimeError("presence semantics failed")
        if not client.set(dedup_key, "1", nx=True, ex=30):
            raise RuntimeError("initial NX/EX claim failed")
        if client.set(dedup_key, "1", nx=True, ex=30) is not None:
            raise RuntimeError("duplicate NX/EX claim unexpectedly succeeded")
        pubsub = client.pubsub()
        pubsub.subscribe(channel)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            message = pubsub.get_message(timeout=1)
            if message and message.get("type") == "subscribe":
                break
        client.publish(channel, "delivery")
        delivered = False
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            message = pubsub.get_message(timeout=1)
            if message and message.get("type") == "message" and message.get("data") == "delivery":
                delivered = True
                break
        pubsub.close()
        if not delivered:
            raise RuntimeError("pub/sub delivery failed")
        if not conversation_client.set(conversation_key, "ok", ex=30):
            raise RuntimeError("logical database write failed")
        if conversation_client.get(conversation_key) != "ok":
            raise RuntimeError("logical database read failed")
    finally:
        client.delete(value_key, metadata_key, presence_key, dedup_key)
        conversation_client.delete(conversation_key)
        client.close()
        conversation_client.close()

    print("Authenticated TLS Valkey connectivity and ephemeral semantics validation completed.")
  PYTHON
}

ephemeral "random_password" "redis" {
  length  = 48
  special = false
}

resource "aws_elasticache_subnet_group" "globalchat" {
  name        = "globalchat-production-redis-subnet-group"
  description = "GlobalChat production private data subnets"
  subnet_ids  = [aws_subnet.private_data["a"].id, aws_subnet.private_data["b"].id]

  tags = {
    Name = "globalchat-production-redis-subnet-group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_ecs" {
  security_group_id            = aws_security_group.redis.id
  description                  = "Valkey from GlobalChat ECS tasks"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 6379
  ip_protocol                  = "tcp"
  to_port                      = 6379
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_redis" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "GlobalChat ECS tasks to Valkey"
  referenced_security_group_id = aws_security_group.redis.id
  from_port                    = 6379
  ip_protocol                  = "tcp"
  to_port                      = 6379
}

resource "aws_elasticache_parameter_group" "globalchat" {
  name        = "globalchat-production-valkey8"
  family      = "valkey8"
  description = "GlobalChat production Valkey parameters"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  tags = {
    Name = "globalchat-production-valkey8"
  }
}

resource "aws_elasticache_user" "globalchat" {
  user_id              = "globalchat-production-default"
  user_name            = "default"
  access_string        = "on ~* &* +@all -@dangerous"
  engine               = "valkey"
  passwords_wo         = ephemeral.random_password.redis.result
  passwords_wo_version = 2

  tags = {
    Name = "globalchat-production-valkey-user"
  }
}

resource "aws_elasticache_user_group" "globalchat" {
  user_group_id = "globalchat-production"
  engine        = "valkey"
  user_ids      = [aws_elasticache_user.globalchat.user_id]

  tags = {
    Name = "globalchat-production-valkey-user-group"
  }
}

resource "aws_elasticache_replication_group" "globalchat" {
  replication_group_id = "globalchat-production-valkey"
  description          = "GlobalChat production ephemeral distributed state"

  engine         = "valkey"
  engine_version = "8.2"
  node_type      = "cache.t4g.micro"
  port           = 6379

  num_cache_clusters         = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false
  cluster_mode               = "disabled"

  subnet_group_name    = aws_elasticache_subnet_group.globalchat.name
  security_group_ids   = [aws_security_group.redis.id]
  parameter_group_name = aws_elasticache_parameter_group.globalchat.name
  user_group_ids       = [aws_elasticache_user_group.globalchat.user_group_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"
  snapshot_retention_limit   = 0
  maintenance_window         = "sun:04:30-sun:05:30"
  auto_minor_version_upgrade = true
  apply_immediately          = true

  tags = {
    Name = "globalchat-production-valkey"
  }
}

resource "aws_secretsmanager_secret" "redis_connection" {
  name                    = "globalchat/production/cache/redis"
  description             = "GlobalChat production authenticated TLS Valkey connection configuration"
  recovery_window_in_days = 30

  tags = {
    Name = "globalchat-production-cache-redis"
  }
}

resource "aws_secretsmanager_secret_version" "redis_connection" {
  secret_id = aws_secretsmanager_secret.redis_connection.id
  secret_string_wo = jsonencode({
    engine        = "valkey"
    host          = aws_elasticache_replication_group.globalchat.primary_endpoint_address
    port          = 6379
    username      = "default"
    redis_url_db0 = "rediss://default:${ephemeral.random_password.redis.result}@${aws_elasticache_replication_group.globalchat.primary_endpoint_address}:6379/0"
    redis_url_db1 = "rediss://default:${ephemeral.random_password.redis.result}@${aws_elasticache_replication_group.globalchat.primary_endpoint_address}:6379/1"
    tls           = true
  })
  secret_string_wo_version = 2
}

data "aws_iam_policy_document" "cache_validation_assume_role" {
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

resource "aws_iam_role" "cache_validation" {
  name               = "globalchat-production-cache-validation"
  description        = "One-off GlobalChat Valkey connectivity validation task role"
  assume_role_policy = data.aws_iam_policy_document.cache_validation_assume_role.json

  tags = {
    Name = "globalchat-production-cache-validation"
  }
}

data "aws_iam_policy_document" "cache_validation" {
  statement {
    sid       = "ReadValkeyConnectionSecret"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.redis_connection.arn]
  }
}

resource "aws_iam_role_policy" "cache_validation" {
  name   = "globalchat-production-cache-validation"
  role   = aws_iam_role.cache_validation.id
  policy = data.aws_iam_policy_document.cache_validation.json
}

resource "aws_cloudwatch_log_group" "cache_validation" {
  name              = "/globalchat/production/cache-validation"
  retention_in_days = 7

  tags = {
    Name = "globalchat-production-cache-validation-logs"
  }
}

resource "aws_ecs_task_definition" "cache_validation" {
  family                   = "globalchat-production-cache-validation"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.cache_validation.arn

  container_definitions = jsonencode([
    {
      name       = "cache-validation"
      image      = "public.ecr.aws/docker/library/python:3.12-slim"
      essential  = true
      entryPoint = ["/bin/sh", "-c"]
      command = [
        "pip install --quiet 'boto3>=1.35,<2' 'redis>=5.2,<7' && echo \"$VALIDATION_SCRIPT_B64\" | base64 -d > /tmp/validate.py && python /tmp/validate.py",
      ]
      environment = [
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "REDIS_SECRET_ARN"
          value = aws_secretsmanager_secret.redis_connection.arn
        },
        {
          name  = "VALIDATION_SCRIPT_B64"
          value = base64encode(local.cache_validation_script)
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.cache_validation.name
          "awslogs-region"        = "ap-south-1"
          "awslogs-stream-prefix" = "validation"
        }
      }
    },
  ])

  depends_on = [aws_secretsmanager_secret_version.redis_connection]

  tags = {
    Name = "globalchat-production-cache-validation"
  }
}

data "aws_iam_policy_document" "github_cache_foundation" {
  statement {
    sid = "ManageGlobalChatValkey"
    actions = [
      "elasticache:AddTagsToResource",
      "elasticache:CreateCacheParameterGroup",
      "elasticache:CreateCacheSubnetGroup",
      "elasticache:CreateReplicationGroup",
      "elasticache:CreateUser",
      "elasticache:CreateUserGroup",
      "elasticache:DeleteCacheParameterGroup",
      "elasticache:DeleteCacheSubnetGroup",
      "elasticache:DeleteReplicationGroup",
      "elasticache:DeleteUser",
      "elasticache:DeleteUserGroup",
      "elasticache:DescribeCacheParameters",
      "elasticache:DescribeCacheParameterGroups",
      "elasticache:DescribeCacheSubnetGroups",
      "elasticache:DescribeReplicationGroups",
      "elasticache:DescribeUsers",
      "elasticache:DescribeUserGroups",
      "elasticache:ListTagsForResource",
      "elasticache:ModifyCacheParameterGroup",
      "elasticache:ModifyCacheSubnetGroup",
      "elasticache:ModifyReplicationGroup",
      "elasticache:ModifyUser",
      "elasticache:ModifyUserGroup",
      "elasticache:RemoveTagsFromResource",
    ]
    resources = [
      "arn:aws:elasticache:ap-south-1:${local.account_id}:parametergroup:globalchat-production-valkey8",
      "arn:aws:elasticache:ap-south-1:${local.account_id}:replicationgroup:globalchat-production-valkey",
      "arn:aws:elasticache:ap-south-1:${local.account_id}:subnetgroup:globalchat-production-redis-subnet-group",
      "arn:aws:elasticache:ap-south-1:${local.account_id}:user:globalchat-production-default",
      "arn:aws:elasticache:ap-south-1:${local.account_id}:usergroup:globalchat-production",
    ]
  }

  statement {
    sid = "ManageGlobalChatCacheSecret"
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
    resources = [
      "arn:aws:secretsmanager:ap-south-1:${local.account_id}:secret:globalchat/production/cache/*",
    ]
  }

  statement {
    sid = "ManageCacheValidationRole"
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
    resources = [
      "arn:aws:iam::${local.account_id}:role/globalchat-production-cache-validation",
    ]
  }

  statement {
    sid = "ManageCacheValidationTaskDefinition"
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
    sid = "ManageCacheNetworkRules"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = [
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.ecs.id}",
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.redis.id}",
    ]
  }

  statement {
    sid       = "DiscoverCacheNetwork"
    actions   = ["ec2:DescribeSecurityGroupRules", "ec2:DescribeSecurityGroups"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_cache_foundation" {
  name   = "globalchat-production-cache-foundation"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_cache_foundation.json
}
