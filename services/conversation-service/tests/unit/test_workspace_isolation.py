import pytest

from app.core import DomainError
from app.services import Authorization


def test_inactive_conversation_member_is_not_found():
    with pytest.raises(DomainError) as error:
        Authorization.view(None)
    assert error.value.status == 404
