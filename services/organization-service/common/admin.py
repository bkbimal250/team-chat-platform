from django.contrib import admin


class OperatorReadOnlyAdmin(admin.ModelAdmin):
    """No hidden ORM writes that bypass application commands, audit, or the outbox."""

    actions = None
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
