import asyncio

import pytest
from fastapi import HTTPException

from app.main import internal


def test_internal_endpoint_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "expected")
    with pytest.raises(HTTPException) as error:
        asyncio.run(internal("wrong"))
    assert error.value.status_code == 401
