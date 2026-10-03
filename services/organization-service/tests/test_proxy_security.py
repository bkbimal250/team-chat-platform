from django.http import HttpResponse
from django.middleware.security import SecurityMiddleware
from django.test import RequestFactory, override_settings

from config.settings import production


def test_production_proxy_header_keeps_public_https_requests_on_the_service():
    assert production.SECURE_SSL_REDIRECT is True
    assert production.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")

    with override_settings(
        ALLOWED_HOSTS=["api.michat.in"],
        SECURE_SSL_REDIRECT=production.SECURE_SSL_REDIRECT,
        SECURE_PROXY_SSL_HEADER=production.SECURE_PROXY_SSL_HEADER,
    ):
        request = RequestFactory().get(
            "/api/v1/organizations/current",
            HTTP_HOST="api.michat.in",
            HTTP_X_FORWARDED_PROTO="https",
        )
        response = SecurityMiddleware(lambda _: HttpResponse(status=401))(request)

    assert response.status_code == 401
    assert response.headers.get("Location") is None
