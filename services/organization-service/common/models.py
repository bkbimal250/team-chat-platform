from django.db import models

from common.ids import new_id


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, context):
        return self.filter(organization_id=context.organization_id)


class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=new_id, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantEntity(Entity):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    objects = TenantQuerySet.as_manager()

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "id"], name="%(app_label)s_%(class)s_tenant_id"
            )
        ]


class ResourceStatus(models.TextChoices):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    DELETED = "DELETED"
