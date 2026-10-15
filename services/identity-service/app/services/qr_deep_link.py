from urllib.parse import urlencode
from uuid import UUID


def build_qr_challenge_payload(base_url: str, challenge_id: UUID, secret: str) -> str:
    root = base_url.rstrip("/")
    query = urlencode({"challenge": f"{challenge_id}.{secret}"})
    return f"{root}?{query}"
