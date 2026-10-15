import pytest

from app.core.errors import DomainError
from app.security.contact_phone import phone_digest
from app.security.phone import normalize_phone


@pytest.mark.parametrize(
    "value,country,expected",
    [
        ("+91 98765 43210", None, "+919876543210"),
        ("09876543210", "IN", "+919876543210"),
        ("9876543210", "IN", "+919876543210"),
        ("020 7946 0018", "GB", "+442079460018"),
        ("(202) 555-0123", "US", "+12025550123"),
    ],
)
def test_single_canonical_normalizer(value, country, expected):
    assert normalize_phone(value, country) == expected


@pytest.mark.parametrize("value", ["9876543210", "+1202*", "0123", "+999123456789"])
def test_ambiguous_or_partial_number_rejected(value):
    with pytest.raises(DomainError):
        normalize_phone(value)


def test_hmac_is_keyed_and_canonical_and_does_not_contain_phone():
    a = phone_digest("+1 202 555 0123", "first-key" * 5)
    assert a == phone_digest("+12025550123", "first-key" * 5)
    assert a != phone_digest("+12025550123", "second-key" * 5)
    assert len(a) == 64 and "12025550123" not in a
