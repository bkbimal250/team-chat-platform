import os
from pathlib import Path
from urllib.parse import quote

import dj_database_url

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
SERVICE_NAME = "organization-service"
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "apps.organizations",
    "apps.branches",
    "apps.teams",
    "apps.members",
    "apps.roles",
    "apps.invitations",
    "apps.audit",
    "events.outbox",
]
MIDDLEWARE = [
    "common.middleware.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
database_url = os.getenv("DATABASE_URL")
if not database_url:
    database_url = "postgresql://{user}:{password}@{host}:{port}/{name}".format(
        user=quote(os.environ["DB_USER"], safe=""),
        password=quote(os.environ["DB_PASSWORD"], safe=""),
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        name=os.environ["DB_NAME"],
    )
DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=60)}
DATABASES["default"]["OPTIONS"] = {"connect_timeout": 5}
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise RuntimeError("Organization Service requires PostgreSQL")
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["common.context.DevelopmentContextAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["common.authorization.TenantPermission"],
    "DEFAULT_SCHEMA_CLASS": "common.schema.OrganizationAutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.TenantCursorPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "120/min"},
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Organization Service",
    "VERSION": "1.0.0",
    "DESCRIPTION": "Phase 1 tenant administration. Production product access is fail-closed pending verified Identity integration. All operations require the documented permission and trusted tenant context. Lists use cursor pagination.",
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "OrganizationStatus": ["ACTIVE", "SUSPENDED", "DISABLED", "DELETED"],
        "MemberStatus": ["INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED"],
        "ResourceStatus": "common.models.ResourceStatus.choices",
        "InvitationStatus": ["PENDING", "ACCEPTED", "EXPIRED", "REVOKED"],
        "TeamMembershipStatus": ["ACTIVE", "LEFT"],
    },
}
DEV_CONTEXT_ENABLED = False
CORS_ALLOWED_ORIGINS = [x for x in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if x]
RABBITMQ_URL = os.environ["RABBITMQ_URL"]
INTERNAL_SERVICE_TOKEN = os.environ.get("INTERNAL_SERVICE_TOKEN", "")
RABBITMQ_EXCHANGE = "organization.events"
OUTBOX_MAX_RETRIES = int(os.getenv("OUTBOX_MAX_RETRIES", "10"))
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "common.middleware.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
