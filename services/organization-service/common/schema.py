from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema


class DevelopmentContextScheme(OpenApiAuthenticationExtension):
    target_class = "common.context.DevelopmentContextAuthentication"
    name = "DevelopmentOnly"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-Dev-Member-ID",
            "description": "Unsafe local-only identity injection. Disabled in production. Uses an ACTIVE database member and current database permissions.",
        }


class OrganizationAutoSchema(AutoSchema):
    def get_description(self):
        permission = (
            self.view.required_permission() if hasattr(self.view, "required_permission") else "none"
        )
        return (
            super().get_description()
            + f"\nRequired permission: `{permission}`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`."
        )
