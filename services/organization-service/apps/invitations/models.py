from django.db import models

from common.models import TenantEntity


class Invitation(TenantEntity):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        ACCEPTED = "ACCEPTED"
        EXPIRED = "EXPIRED"
        REVOKED = "REVOKED"

    team = models.ForeignKey("teams.Team", on_delete=models.PROTECT, null=True, blank=True)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, null=True, blank=True)
    invited_by_member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    intended_role = models.ForeignKey("roles.Role", on_delete=models.PROTECT)
    accepted_member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    expires_at = models.DateTimeField(db_index=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantEntity.Meta):
        indexes = [models.Index(fields=["organization", "status"])]
