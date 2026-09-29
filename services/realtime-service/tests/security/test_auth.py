import pytest

from app.auth import authenticate
from app.core import ProtocolError


def test_invalid_handshake_token_is_rejected():
    with pytest.raises(ProtocolError):
        authenticate("not-a-jwt")
