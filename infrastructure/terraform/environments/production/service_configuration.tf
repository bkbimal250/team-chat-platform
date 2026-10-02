locals {
  application_secret_names = {
    identity_jwt_private = "globalchat/production/identity/jwt-private-key"
    jwt_public           = "globalchat/production/auth/jwt-public-key"
    organization_django  = "globalchat/production/organization/django-secret-key"
    organization_token   = "globalchat/production/organization/internal-token"
    user_token           = "globalchat/production/user/internal-token"
    conversation_token   = "globalchat/production/conversation/internal-token"
    messaging_token      = "globalchat/production/messaging/internal-token"
    identity_sms         = "globalchat/production/identity/sms"
    notification_fcm     = "globalchat/production/notification/firebase"
  }

  trusted_web_origins = "https://michat.in,https://app.michat.in,https://admin.michat.in"
  jwt_common = {
    JWT_ALGORITHM = "RS256"
    JWT_ISSUER    = "identity-service"
    JWT_AUDIENCE  = "team-chat-platform"
  }
  internal_urls = {
    organization = "http://organization.globalchat.internal:8000"
    identity     = "http://identity.globalchat.internal:8001"
    user         = "http://user.globalchat.internal:8002"
    conversation = "http://conversation.globalchat.internal:8003"
    messaging    = "http://messaging.globalchat.internal:8004"
    media        = "http://media.globalchat.internal:8005"
    notification = "http://notification.globalchat.internal:8006"
    realtime     = "http://realtime.globalchat.internal:8007"
  }

  service_configuration = {
    organization = {
      port          = 8000
      task_role_arn = null
      environment = merge(local.jwt_common, {
        DJANGO_SETTINGS_MODULE = "config.settings.production"
        ENVIRONMENT            = "production"
        ALLOWED_HOSTS          = "api.michat.in,organization.globalchat.internal"
        CORS_ALLOWED_ORIGINS   = local.trusted_web_origins
        LOG_LEVEL              = "INFO"
      })
      secrets = {
        DATABASE_URL           = "${aws_secretsmanager_secret.service_database["organization"].arn}:database_url::"
        RABBITMQ_URL           = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::"
        JWT_PUBLIC_KEY         = aws_secretsmanager_secret.application["jwt_public"].arn
        SECRET_KEY             = aws_secretsmanager_secret.application["organization_django"].arn
        INTERNAL_SERVICE_TOKEN = aws_secretsmanager_secret.application["organization_token"].arn
      }
      processes = { api = "gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 30 --access-logfile -", outbox = "python manage.py publish_outbox" }
      health    = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql" }
    }
    identity = {
      port          = 8001
      task_role_arn = null
      environment = {
        APP_ENV                  = "production"
        SERVICE_NAME             = "identity-service"
        ACCESS_TOKEN_ALG         = "RS256"
        ACCESS_TOKEN_TTL         = "900"
        REFRESH_TOKEN_TTL        = "2592000"
        OTP_PROVIDER             = "sms"
        SMS_PROVIDER             = "hilite_http"
        SMS_TIMEOUT_SECONDS      = "5"
        OTP_TTL                  = "300"
        OTP_MAX_ATTEMPTS         = "5"
        OTP_RESEND_COOLDOWN      = "60"
        REGISTRATION_POLICY      = "invite_only"
        ORGANIZATION_SERVICE_URL = local.internal_urls.organization
        CORS_ALLOWED_ORIGINS     = local.trusted_web_origins
      }
      secrets = {
        DATABASE_URL             = "${aws_secretsmanager_secret.service_database["identity"].arn}:database_url::"
        REDIS_URL                = "${aws_secretsmanager_secret.redis_connection.arn}:redis_url_db0::"
        RABBITMQ_URL             = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::"
        ACCESS_TOKEN_PRIVATE_KEY = aws_secretsmanager_secret.application["identity_jwt_private"].arn
        ACCESS_TOKEN_PUBLIC_KEY  = aws_secretsmanager_secret.application["jwt_public"].arn
        SERVICE_AUTH_TOKEN       = aws_secretsmanager_secret.application["organization_token"].arn
        SMS_USERNAME             = "${aws_secretsmanager_secret.application["identity_sms"].arn}:username::"
        SMS_API_KEY              = "${aws_secretsmanager_secret.application["identity_sms"].arn}:api_key::"
      }
      processes = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8001", outbox = "python -m app.events.run_worker" }
      health    = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql,valkey" }
    }
    user = {
      port          = 8002
      task_role_arn = null
      environment   = { APP_ENV = "production", IDENTITY_JWT_ALGORITHM = "RS256", IDENTITY_JWT_ISSUER = "identity-service", RABBITMQ_EXCHANGE = "platform.events", RABBITMQ_PREFETCH_COUNT = "20", OUTBOX_BATCH_SIZE = "50", OUTBOX_POLL_SECONDS = "1" }
      secrets       = { DATABASE_URL = "${aws_secretsmanager_secret.service_database["user"].arn}:database_url::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", IDENTITY_JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn, INTERNAL_SERVICE_TOKEN = aws_secretsmanager_secret.application["user_token"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8002", outbox = "python -m app.outbox_runner" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql" }
    }
    conversation = {
      port          = 8003
      task_role_arn = null
      environment   = merge(local.jwt_common, { APP_ENV = "production", SERVICE_NAME = "conversation-service", IDENTITY_SERVICE_URL = local.internal_urls.identity, ORGANIZATION_SERVICE_URL = local.internal_urls.organization, USER_SERVICE_URL = local.internal_urls.user, CORS_ALLOWED_ORIGINS = local.trusted_web_origins })
      secrets       = { DATABASE_URL = "${aws_secretsmanager_secret.service_database["conversation"].arn}:database_url::", REDIS_URL = "${aws_secretsmanager_secret.redis_connection.arn}:redis_url_db1::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn, INTERNAL_SERVICE_TOKEN = aws_secretsmanager_secret.application["conversation_token"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8003", outbox = "python -m app.outbox_runner" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql,valkey" }
      pending_external_configuration = [
        "SMS_API_BASE_URL",
        "SMS_ROUTE",
        "SMS_SENDER_ID",
        "SMS_TEMPLATE_ID",
        "SMS_MESSAGE_TEMPLATE",
      ]
    }
    messaging = {
      port          = 8004
      task_role_arn = null
      environment   = merge(local.jwt_common, { APP_ENV = "production" })
      secrets       = { DATABASE_URL = "${aws_secretsmanager_secret.service_database["messaging"].arn}:database_url::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn, INTERNAL_SERVICE_TOKEN = aws_secretsmanager_secret.application["messaging_token"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8004", outbox = "python -m app.outbox_runner" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql" }
    }
    realtime = {
      port          = 8007
      task_role_arn = null
      environment   = merge(local.jwt_common, { APP_ENV = "production", INSTANCE_ID = "ECS_TASK_ID" })
      secrets       = { REDIS_URL = "${aws_secretsmanager_secret.redis_connection.arn}:redis_url_db0::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8007", consumer = "python -m app.consumer_runner" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "valkey" }
    }
    media = {
      port          = 8005
      task_role_arn = aws_iam_role.media_task.arn
      environment   = merge(local.jwt_common, { APP_ENV = "production", MEDIA_STORAGE_BACKEND = "s3", AWS_REGION = "ap-south-1", MEDIA_S3_BUCKET = aws_s3_bucket.media.id })
      secrets       = { DATABASE_URL = "${aws_secretsmanager_secret.service_database["media"].arn}:database_url::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8005" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "s3" }
    }
    notification = {
      port          = 8006
      task_role_arn = null
      environment   = merge(local.jwt_common, { APP_ENV = "production", PUSH_PROVIDER = "fcm", DELIVERY_POLL_SECONDS = "1" })
      secrets       = { DATABASE_URL = "${aws_secretsmanager_secret.service_database["notification"].arn}:database_url::", RABBITMQ_URL = "${aws_secretsmanager_secret.rabbitmq_connection.arn}:rabbitmq_url::", JWT_PUBLIC_KEY = aws_secretsmanager_secret.application["jwt_public"].arn, FIREBASE_CREDENTIALS_JSON = aws_secretsmanager_secret.application["notification_fcm"].arn }
      processes     = { api = "uvicorn app.main:app --host 0.0.0.0 --port 8006", consumer = "python -m app.consumer_runner", delivery_worker = "python -m app.delivery_worker" }
      health        = { live = "/health/live", ready = "/health/ready", dependencies = "postgresql" }
    }
  }

  process_definitions = {
    organization-api      = { service = "organization", name = "api", command = local.service_configuration.organization.processes.api, port = 8000, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = "api" }
    organization-outbox   = { service = "organization", name = "outbox", command = local.service_configuration.organization.processes.outbox, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    identity-api          = { service = "identity", name = "api", command = local.service_configuration.identity.processes.api, port = 8001, cpu = 256, memory = 512, database = true, valkey = true, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    identity-outbox       = { service = "identity", name = "outbox", command = local.service_configuration.identity.processes.outbox, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    identity-consumer     = { service = "identity", name = "consumer", command = "python -m app.consumer_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    user-api              = { service = "user", name = "api", command = local.service_configuration.user.processes.api, port = 8002, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    user-outbox           = { service = "user", name = "outbox", command = local.service_configuration.user.processes.outbox, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    user-consumer         = { service = "user", name = "consumer", command = "python -m app.consumer_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    conversation-api      = { service = "conversation", name = "api", command = local.service_configuration.conversation.processes.api, port = 8003, cpu = 256, memory = 512, database = true, valkey = true, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    conversation-outbox   = { service = "conversation", name = "outbox", command = local.service_configuration.conversation.processes.outbox, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    conversation-consumer = { service = "conversation", name = "consumer", command = "python -m app.consumer_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    messaging-api         = { service = "messaging", name = "api", command = local.service_configuration.messaging.processes.api, port = 8004, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    messaging-outbox      = { service = "messaging", name = "outbox", command = local.service_configuration.messaging.processes.outbox, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    messaging-consumer    = { service = "messaging", name = "consumer", command = "python -m app.consumer_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    realtime-api          = { service = "realtime", name = "api", command = local.service_configuration.realtime.processes.api, port = 8007, cpu = 512, memory = 1024, database = false, valkey = true, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = "realtime" }
    realtime-consumer     = { service = "realtime", name = "consumer", command = local.service_configuration.realtime.processes.consumer, port = null, cpu = 256, memory = 512, database = false, valkey = true, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    media-api             = { service = "media", name = "api", command = local.service_configuration.media.processes.api, port = 8005, cpu = 512, memory = 1024, database = true, valkey = false, rabbitmq = false, s3 = true, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    media-consumer        = { service = "media", name = "consumer", command = "python -m app.consumer_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = true, health = "essential-process", cloud_map = false, alb = null }
    media-outbox          = { service = "media", name = "outbox", command = "python -m app.outbox_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    notification-api      = { service = "notification", name = "api", command = local.service_configuration.notification.processes.api, port = 8006, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = false, s3 = false, health = "http:/health/live,/health/ready", cloud_map = true, alb = null }
    notification-consumer = { service = "notification", name = "consumer", command = local.service_configuration.notification.processes.consumer, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    notification-delivery = { service = "notification", name = "delivery-worker", command = local.service_configuration.notification.processes.delivery_worker, port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = false, s3 = false, health = "essential-process", cloud_map = false, alb = null }
    notification-outbox   = { service = "notification", name = "outbox", command = "python -m app.outbox_runner", port = null, cpu = 256, memory = 512, database = true, valkey = false, rabbitmq = true, s3 = false, health = "essential-process", cloud_map = false, alb = null }
  }

  deployment_processes = {
    for key, process in local.process_definitions : key => merge(process, {
      ecr_repository = aws_ecr_repository.backend[process.service].repository_url
      environment    = local.service_configuration[process.service].environment
      secrets        = local.service_configuration[process.service].secrets
      task_role_arn  = local.service_configuration[process.service].task_role_arn
      pending_external_configuration = try(
        local.service_configuration[process.service].pending_external_configuration,
        [],
      )
    })
  }
}

resource "aws_secretsmanager_secret" "application" {
  for_each                = local.application_secret_names
  name                    = each.value
  description             = "GlobalChat production ${replace(each.key, "_", " ")}"
  recovery_window_in_days = 30
  tags                    = { Name = "globalchat-production-${replace(each.key, "_", "-")}" }
}

data "aws_iam_policy_document" "ecs_execution_secrets" {
  statement {
    sid       = "ReadGlobalChatProductionTaskSecrets"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = concat(values(aws_secretsmanager_secret.service_database)[*].arn, [aws_secretsmanager_secret.redis_connection.arn, aws_secretsmanager_secret.rabbitmq_connection.arn], values(aws_secretsmanager_secret.application)[*].arn)
  }
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name   = "globalchat-production-task-secret-injection"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
}
