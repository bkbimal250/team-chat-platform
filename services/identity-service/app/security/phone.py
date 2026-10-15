import phonenumbers

from app.core.errors import DomainError


def normalize_phone(value: str, country: str | None = None) -> str:
    try:
        parsed = phonenumbers.parse(value, country)
    except phonenumbers.NumberParseException as exc:
        raise DomainError(
            "PHONE_INVALID", "Provide a valid international phone number.", 422
        ) from exc
    if parsed.extension or not phonenumbers.is_valid_number(parsed):
        raise DomainError("PHONE_INVALID", "Provide a valid international phone number.", 422)
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    return f"{phone[:3]}{'*' * max(0, len(phone) - 5)}{phone[-2:]}"
