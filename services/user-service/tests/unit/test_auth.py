import pytest
from fastapi import HTTPException

from app.auth import require_authenticated_context


def test_missing_bearer_is_rejected():
    with pytest.raises(HTTPException) as error:
        require_authenticated_context(None)
    assert error.value.status_code == 401
