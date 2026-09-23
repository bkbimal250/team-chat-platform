from django.shortcuts import get_object_or_404


def tenant_queryset(model, context):
    """Single API read boundary; every tenant collection starts here."""
    return model.objects.for_tenant(context)


def tenant_get(model, context, pk, *, lock=False):
    queryset = tenant_queryset(model, context)
    if lock:
        queryset = queryset.select_for_update()
    return get_object_or_404(queryset, pk=pk)
