from rest_framework.pagination import CursorPagination


class TenantCursorPagination(CursorPagination):
    page_size = 50
    ordering = ("-created_at", "-id")
    page_size_query_param = "page_size"
    max_page_size = 100
