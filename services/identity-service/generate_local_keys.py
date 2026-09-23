"""Generate ignored development-only Ed25519 JWT keys without printing private material."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

directory = Path(__file__).parent / ".local-keys"
directory.mkdir(exist_ok=True)
private_path = directory / "private.pem"
public_path = directory / "public.pem"
if not private_path.exists():
    private = Ed25519PrivateKey.generate()
    private_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
