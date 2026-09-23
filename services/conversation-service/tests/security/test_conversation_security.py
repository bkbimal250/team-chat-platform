import pytest

from app.core import DomainError
from app.services import Authorization


def test_non_member_is_denied():
    with pytest.raises(DomainError) as error:
        Authorization.view(None)
    assert error.value.status == 404
