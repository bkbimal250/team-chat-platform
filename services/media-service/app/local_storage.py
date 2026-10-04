"""Development-only private filesystem storage with bounded, signed capabilities."""

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.storage import ObjectInfo, StorageError


class LocalPrivateStorage:
    def __init__(self, root: str, secret: str, base_url: str):
        if len(secret) < 32:
            raise ValueError("local storage signing secret is too short")
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.secret = secret.encode()
        self.base_url = base_url.rstrip("/")

    def location(self, bucket: str, key: str) -> Path:
        # Never interpolate user-controlled object keys into filesystem paths.
        return self.root / hashlib.sha256((bucket + "\0" + key).encode()).hexdigest()

    def capability(self, action, bucket, key, expires, **fields):
        ttl = (
            expires if isinstance(expires, int) else max(1, int(expires.timestamp() - time.time()))
        )
        body = {
            "action": action,
            "bucket": bucket,
            "key": key,
            "exp": int(time.time()) + min(ttl, 900),
            **fields,
        }
        raw = (
            base64.urlsafe_b64encode(json.dumps(body, separators=(",", ":")).encode())
            .rstrip(b"=")
            .decode()
        )
        signature = hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()
        return f"{self.base_url}/local-storage/{raw}.{signature}"

    def verify(self, token: str, action: str):
        try:
            raw, signature = token.split(".")
            expected = hmac.new(self.secret, raw.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError()
            body = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
            if body["action"] != action or body["exp"] <= time.time():
                raise ValueError()
            return body
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise StorageError("invalid or expired storage capability") from exc

    async def presign_upload(self, bucket: str, key: str, mime_type: str, expires: datetime):
        return (
            self.capability("put", bucket, key, expires, mime=mime_type),
            {"Content-Type": mime_type},
            expires,
        )

    async def head(self, bucket: str, key: str):
        path = self.location(bucket, key)
        if not path.exists() or not path.with_suffix(".json").exists():
            return None
        metadata = json.loads(path.with_suffix(".json").read_text())
        return ObjectInfo(path.stat().st_size, metadata["mime"])

    async def presign_download(self, bucket: str, key: str, expires: int):
        return self.capability("get", bucket, key, expires)

    async def delete(self, bucket: str, key: str):
        path = self.location(bucket, key)
        path.unlink(missing_ok=True)
        path.with_suffix(".json").unlink(missing_ok=True)

    async def create_multipart_upload(self, bucket, key, mime_type):
        upload_id = str(uuid4())
        path = self.location(bucket, key).with_suffix(".parts") / upload_id
        path.mkdir(parents=True)
        (path / "metadata.json").write_text(json.dumps({"mime": mime_type}))
        return upload_id

    def parts_path(self, bucket, key, upload_id):
        # Reject traversal even for authenticated multipart metadata.
        from uuid import UUID

        upload_id = str(UUID(upload_id))
        path = self.location(bucket, key).with_suffix(".parts") / upload_id
        if not path.exists():
            raise StorageError("multipart upload unavailable")
        return path

    async def presign_upload_part(self, bucket, key, upload_id, part_number, expires):
        self.parts_path(bucket, key, upload_id)
        return self.capability(
            "part", bucket, key, expires, upload_id=upload_id, part_number=part_number
        )

    async def list_parts(self, bucket, key, upload_id):
        path = self.parts_path(bucket, key, upload_id)
        return [
            {
                "part_number": int(p.stem),
                "etag": hashlib.sha256(p.read_bytes()).hexdigest(),
                "size": p.stat().st_size,
            }
            for p in sorted(path.glob("*.part"), key=lambda p: int(p.stem))
        ]

    async def complete_multipart_upload(self, bucket, key, upload_id, parts):
        path = self.parts_path(bucket, key, upload_id)
        actual = {p["part_number"]: p for p in await self.list_parts(bucket, key, upload_id)}
        for p in parts:
            if p["part_number"] not in actual or actual[p["part_number"]]["etag"] != p[
                "etag"
            ].strip('"'):
                raise StorageError("multipart part mismatch")
        target = self.location(bucket, key)
        with target.open("wb") as handle:
            for p in parts:
                with (path / f"{p['part_number']}.part").open("rb") as source:
                    import shutil

                    shutil.copyfileobj(source, handle)
        target.with_suffix(".json").write_text((path / "metadata.json").read_text())
        await self.abort_multipart_upload(bucket, key, upload_id)

    async def abort_multipart_upload(self, bucket, key, upload_id):
        import shutil

        path = self.parts_path(bucket, key, upload_id)
        if not path.resolve().is_relative_to(self.root):
            raise StorageError("multipart path outside local storage")
        shutil.rmtree(path)  # path is constrained under the resolved local root and UUID upload ID.

    async def ready(self):
        return self.root.is_dir()
