from django.conf import settings
from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.audit.api import AuditViewSet
from apps.branches.api import BranchViewSet
from apps.invitations.api import InvitationViewSet
from apps.members.api import MemberViewSet
from apps.organizations.api import OrganizationViewSet
from apps.organizations.internal_api import identity_memberships
from apps.roles.api import PermissionViewSet, RoleAssignmentViewSet, RoleViewSet
from apps.teams.api import TeamViewSet

router = DefaultRouter()
for prefix, view in [
    ("organizations", OrganizationViewSet),
    ("branches", BranchViewSet),
    ("teams", TeamViewSet),
    ("members", MemberViewSet),
    ("invitations", InvitationViewSet),
    ("roles", RoleViewSet),
    ("permissions", PermissionViewSet),
    ("role-assignments", RoleAssignmentViewSet),
    ("audit-logs", AuditViewSet),
]:
    router.register(prefix, view, basename=prefix)


def live(request):
    return JsonResponse({"status": "alive"})


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)
    return JsonResponse(
        {
            "status": "ready",
            "database": "available",
            "broker": "asynchronous; monitored by outbox worker",
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path(
        "api/schema/", SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[])
    ),
    path("health/live", live),
    path("health/ready", ready),
    path("api/internal/v1/identity-memberships/<uuid:identity_id>/", identity_memberships),
]
if settings.ENVIRONMENT == "local":
    urlpatterns += [
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(
                url_name="schema", authentication_classes=[], permission_classes=[]
            ),
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(
                url_name="schema", authentication_classes=[], permission_classes=[]
            ),
        ),
    ]
urlpatterns[2].name = "schema"
