from django.db import models

from common.models import Entity, TenantEntity


class Organization(Entity):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        SUSPENDED = "SUSPENDED"
        DISABLED = "DISABLED"
        DELETED = "DELETED"

    class Type(models.TextChoices):
        BUSINESS = "BUSINESS"
        NONPROFIT = "NONPROFIT"
        OTHER = "OTHER"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    organization_type = models.CharField(max_length=20, choices=Type, default=Type.BUSINESS)
    status = models.CharField(max_length=20, choices=Status, default=Status.ACTIVE, db_index=True)
    logo_media_id = models.UUIDField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC")
    country_code = models.CharField(max_length=2, default="IN")
    suspended_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class OrganizationSettings(TenantEntity):
    organization = models.OneToOneField(
        Organization, on_delete=models.PROTECT, related_name="settings"
    )
    allow_member_invites = models.BooleanField(default=True)
    allow_group_creation = models.BooleanField(default=True)
    allow_external_chat = models.BooleanField(default=False)
    max_members = models.PositiveIntegerField(null=True, blank=True)
    max_teams = models.PositiveIntegerField(null=True, blank=True)
    default_timezone = models.CharField(max_length=64, default="UTC")
