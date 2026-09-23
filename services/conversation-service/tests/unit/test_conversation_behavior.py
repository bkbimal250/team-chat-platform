import uuid

from app.services import direct_key


def test_direct_key_is_same_for_a_b_and_b_a():
    a, b = uuid.uuid4(), uuid.uuid4()
    assert direct_key(a, b) == direct_key(b, a)
