from uuid import UUID, uuid4


def new_id() -> UUID:
    """Encapsulated UUID4 until a standard supported UUID7 implementation is selected."""
    return uuid4()
