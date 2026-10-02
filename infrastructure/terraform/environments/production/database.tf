locals {
  postgres_services = {
    organization = {
      database = "teamchat_organization_db"
      username = "globalchat_organization"
    }
    identity = {
      database = "identity_db"
      username = "globalchat_identity"
    }
    user = {
      database = "teamchat_user_db"
      username = "globalchat_user"
    }
    conversation = {
      database = "conversation_db"
      username = "globalchat_conversation"
    }
    messaging = {
      database = "teamchat_message_db"
      username = "globalchat_messaging"
    }
    media = {
      database = "teamchat_media_db"
      username = "globalchat_media"
    }
    notification = {
      database = "teamchat_notification_db"
      username = "globalchat_notification"
    }
  }

  database_bootstrap_script = <<-PYTHON
    import json
    import os
    import secrets
    import string

    import boto3
    import psycopg
    from botocore.exceptions import ClientError
    from psycopg import sql


    region = os.environ["AWS_REGION"]
    master_secret_arn = os.environ["MASTER_SECRET_ARN"]
    services = json.loads(os.environ["SERVICE_DATABASES"])
    secrets_client = boto3.client("secretsmanager", region_name=region)
    master = json.loads(
        secrets_client.get_secret_value(SecretId=master_secret_arn)["SecretString"]
    )
    host = os.environ["RDS_HOST"]
    port = int(os.environ["RDS_PORT"])


    def read_or_generate(service):
        item = services[service]
        try:
            response = secrets_client.get_secret_value(SecretId=item["secret_arn"])
            if response.get("SecretString"):
                stored = json.loads(response["SecretString"])
                if stored.get("password"):
                    return stored
        except ClientError as error:
            if error.response["Error"]["Code"] not in {
                "ResourceNotFoundException",
                "InvalidRequestException",
            }:
                raise
        alphabet = string.ascii_letters + string.digits
        return {
            "engine": "postgres",
            "host": host,
            "port": port,
            "dbname": item["database"],
            "username": item["username"],
            "password": "".join(secrets.choice(alphabet) for _ in range(48)),
        }


    credentials = {service: read_or_generate(service) for service in services}
    admin = psycopg.connect(
        host=host,
        port=port,
        dbname="postgres",
        user=master["username"],
        password=master["password"],
        sslmode="require",
        autocommit=True,
    )
    with admin:
        with admin.cursor() as cursor:
            for service, credential in credentials.items():
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (credential["username"],))
                if cursor.fetchone():
                    cursor.execute(
                        sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                            sql.Identifier(credential["username"]),
                            sql.Literal(credential["password"]),
                        )
                    )
                else:
                    cursor.execute(
                        sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                            sql.Identifier(credential["username"]),
                            sql.Literal(credential["password"]),
                        )
                    )
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (credential["dbname"],))
                if not cursor.fetchone():
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            sql.Identifier(credential["dbname"]),
                            sql.Identifier(credential["username"]),
                        )
                    )
                else:
                    cursor.execute(
                        sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                            sql.Identifier(credential["dbname"]),
                            sql.Identifier(credential["username"]),
                        )
                    )
                cursor.execute(
                    sql.SQL("REVOKE CONNECT ON DATABASE {} FROM PUBLIC").format(
                        sql.Identifier(credential["dbname"])
                    )
                )
                cursor.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(credential["dbname"]),
                        sql.Identifier(credential["username"]),
                    )
                )

    for service, credential in credentials.items():
        with psycopg.connect(
            host=host,
            port=port,
            dbname=credential["dbname"],
            user=credential["username"],
            password=credential["password"],
            sslmode="require",
        ) as own_connection:
            with own_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise RuntimeError(f"own database verification failed for {service}")
        for other_service, other in credentials.items():
            if other_service == service:
                continue
            try:
                psycopg.connect(
                    host=host,
                    port=port,
                    dbname=other["dbname"],
                    user=credential["username"],
                    password=credential["password"],
                    sslmode="require",
                    connect_timeout=5,
                ).close()
            except psycopg.OperationalError:
                continue
            raise RuntimeError(f"cross-database access unexpectedly succeeded for {service}")
        secrets_client.put_secret_value(
            SecretId=services[service]["secret_arn"],
            SecretString=json.dumps(credential, separators=(",", ":")),
        )

    print("Database bootstrap and isolation verification completed for all services.")
  PYTHON
}

resource "aws_db_subnet_group" "globalchat" {
  name        = "globalchat-production-db-subnet-group"
  description = "GlobalChat production private data subnets"
  subnet_ids  = [aws_subnet.private_data["a"].id, aws_subnet.private_data["b"].id]

  tags = {
    Name = "globalchat-production-db-subnet-group"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id            = aws_security_group.rds.id
  description                  = "PostgreSQL from GlobalChat ECS tasks"
  referenced_security_group_id = aws_security_group.ecs.id
  from_port                    = 5432
  ip_protocol                  = "tcp"
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_rds" {
  security_group_id            = aws_security_group.ecs.id
  description                  = "GlobalChat ECS tasks to PostgreSQL"
  referenced_security_group_id = aws_security_group.rds.id
  from_port                    = 5432
  ip_protocol                  = "tcp"
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "ecs_https" {
  security_group_id = aws_security_group.ecs.id
  description       = "HTTPS for image pulls and AWS APIs through NAT"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_db_instance" "postgres" {
  identifier = "globalchat-production-postgres"

  engine         = "postgres"
  engine_version = "16.15"
  instance_class = "db.t4g.small"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  username                    = "globalchat_admin"
  manage_master_user_password = true
  port                        = 5432

  db_subnet_group_name   = aws_db_subnet_group.globalchat.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period    = 7
  backup_window              = "02:00-03:00"
  maintenance_window         = "sun:03:30-sun:04:30"
  auto_minor_version_upgrade = true

  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "globalchat-production-postgres-final"
  copy_tags_to_snapshot     = true

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = false
  monitoring_interval             = 0

  tags = {
    Name = "globalchat-production-postgres"
  }
}

resource "aws_secretsmanager_secret" "service_database" {
  for_each = local.postgres_services

  name                    = "globalchat/production/database/${each.key}"
  description             = "GlobalChat production ${each.key} database credentials"
  recovery_window_in_days = 30

  tags = {
    Name    = "globalchat-production-database-${each.key}"
    Service = each.key
  }
}

data "aws_iam_policy_document" "database_bootstrap_assume_role" {
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

resource "aws_iam_role" "database_bootstrap" {
  name               = "globalchat-production-database-bootstrap"
  description        = "One-off GlobalChat database bootstrap task role"
  assume_role_policy = data.aws_iam_policy_document.database_bootstrap_assume_role.json

  tags = {
    Name = "globalchat-production-database-bootstrap"
  }
}

data "aws_iam_policy_document" "database_bootstrap" {
  statement {
    sid     = "ReadRdsManagedMasterSecret"
    effect  = "Allow"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_db_instance.postgres.master_user_secret[0].secret_arn,
    ]
  }

  statement {
    sid    = "ManageServiceDatabaseSecretValues"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:PutSecretValue",
    ]
    resources = values(aws_secretsmanager_secret.service_database)[*].arn
  }
}

resource "aws_iam_role_policy" "database_bootstrap" {
  name   = "globalchat-production-database-bootstrap"
  role   = aws_iam_role.database_bootstrap.id
  policy = data.aws_iam_policy_document.database_bootstrap.json
}

resource "aws_cloudwatch_log_group" "database_bootstrap" {
  name              = "/globalchat/production/database-bootstrap"
  retention_in_days = 7

  tags = {
    Name = "globalchat-production-database-bootstrap-logs"
  }
}

resource "aws_ecs_task_definition" "database_bootstrap" {
  family                   = "globalchat-production-database-bootstrap"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.database_bootstrap.arn

  container_definitions = jsonencode([
    {
      name       = "database-bootstrap"
      image      = "public.ecr.aws/docker/library/python:3.12-slim"
      essential  = true
      entryPoint = ["/bin/sh", "-c"]
      command = [
        "pip install --quiet 'boto3>=1.35,<2' 'psycopg[binary]>=3.2,<4' && echo \"$BOOTSTRAP_SCRIPT_B64\" | base64 -d > /tmp/bootstrap.py && python /tmp/bootstrap.py",
      ]
      environment = [
        {
          name  = "AWS_REGION"
          value = "ap-south-1"
        },
        {
          name  = "MASTER_SECRET_ARN"
          value = aws_db_instance.postgres.master_user_secret[0].secret_arn
        },
        {
          name  = "RDS_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "RDS_PORT"
          value = tostring(aws_db_instance.postgres.port)
        },
        {
          name = "SERVICE_DATABASES"
          value = jsonencode({
            for service, config in local.postgres_services : service => {
              database   = config.database
              username   = config.username
              secret_arn = aws_secretsmanager_secret.service_database[service].arn
            }
          })
        },
        {
          name  = "BOOTSTRAP_SCRIPT_B64"
          value = base64encode(local.database_bootstrap_script)
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.database_bootstrap.name
          "awslogs-region"        = "ap-south-1"
          "awslogs-stream-prefix" = "bootstrap"
        }
      }
    },
  ])

  tags = {
    Name = "globalchat-production-database-bootstrap"
  }
}

data "aws_iam_policy_document" "github_database_foundation" {
  statement {
    sid = "ManageGlobalChatPostgres"
    actions = [
      "rds:AddTagsToResource",
      "rds:CreateDBInstance",
      "rds:CreateDBSubnetGroup",
      "rds:DeleteDBInstance",
      "rds:DeleteDBSubnetGroup",
      "rds:DescribeDBInstances",
      "rds:DescribeDBSubnetGroups",
      "rds:ListTagsForResource",
      "rds:ModifyDBInstance",
      "rds:ModifyDBSubnetGroup",
      "rds:RemoveTagsFromResource",
    ]
    resources = [
      "arn:aws:rds:ap-south-1:${local.account_id}:db:globalchat-production-postgres",
      "arn:aws:rds:ap-south-1:${local.account_id}:subgrp:globalchat-production-db-subnet-group",
    ]
  }

  statement {
    sid       = "DiscoverRdsCapabilities"
    actions   = ["rds:DescribeOrderableDBInstanceOptions"]
    resources = ["*"]
  }

  statement {
    sid = "ManageGlobalChatDatabaseSecrets"
    actions = [
      "secretsmanager:CreateSecret",
      "secretsmanager:DeleteSecret",
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:ListSecretVersionIds",
      "secretsmanager:PutResourcePolicy",
      "secretsmanager:RemoveRegionsFromReplication",
      "secretsmanager:ReplicateSecretToRegions",
      "secretsmanager:RestoreSecret",
      "secretsmanager:RotateSecret",
      "secretsmanager:StopReplicationToReplica",
      "secretsmanager:TagResource",
      "secretsmanager:UntagResource",
      "secretsmanager:UpdateSecret",
      "secretsmanager:UpdateSecretVersionStage",
    ]
    resources = [
      "arn:aws:secretsmanager:ap-south-1:${local.account_id}:secret:globalchat/production/database/*",
    ]
  }

  statement {
    sid = "ManageDatabaseBootstrapRole"
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
      "arn:aws:iam::${local.account_id}:role/globalchat-production-database-bootstrap",
    ]
  }

  statement {
    sid = "ManageDatabaseBootstrapTaskDefinition"
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
    sid = "ManageDatabaseNetworkRules"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = [
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.ecs.id}",
      "arn:aws:ec2:ap-south-1:${local.account_id}:security-group/${aws_security_group.rds.id}",
    ]
  }

  statement {
    sid       = "DiscoverDatabaseNetwork"
    actions   = ["ec2:DescribeSecurityGroupRules", "ec2:DescribeSecurityGroups"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_database_foundation" {
  name   = "globalchat-production-database-foundation"
  role   = aws_iam_role.github_deploy.id
  policy = data.aws_iam_policy_document.github_database_foundation.json
}
