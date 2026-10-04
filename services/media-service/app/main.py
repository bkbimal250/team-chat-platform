from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import MediaPolicy, MediaSettings, get_settings
from app.db import SessionLocal, engine
from app.durable import DurableMediaService
from app.local_storage import LocalPrivateStorage
from app.schemas import MultipartCompleteRequest, MultipartPartsRequest, UploadRequest
from app.security import Principal, get_principal
from app.service import MediaService
from app.storage import FakePrivateStorage, S3PrivateStorage


def build_media_service(settings: MediaSettings | None = None) -> MediaService:
    settings = settings or get_settings()
    if settings.media_storage_backend == "local":
        storage = LocalPrivateStorage(
            settings.local_storage_root,
            settings.local_storage_secret,
            settings.local_storage_base_url,
        )
        bucket = settings.media_s3_bucket or "globalchat-local-media"
    elif settings.media_storage_backend == "s3":
        storage = S3PrivateStorage(
            region=settings.aws_region,
            bucket=settings.media_s3_bucket,
            endpoint_url=settings.media_s3_endpoint_url,
        )
        bucket = settings.media_s3_bucket
    else:
        storage = FakePrivateStorage()
        bucket = settings.media_s3_bucket or "team-chat-platform-private"
    policy = MediaPolicy(bucket=bucket)
    if settings.app_env == "production" or settings.media_storage_backend in {"s3", "local"}:
        return DurableMediaService(storage, policy, SessionLocal)
    return MediaService(storage, policy)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Settings and storage selection are validated before this process accepts requests.
    application.state.media_service = build_media_service()
    yield
    await engine.dispose()


app = FastAPI(title="Media Service", version="1.0.0", lifespan=lifespan)
# Keep development imports and OpenAPI generation usable; production configuration is
# revalidated at startup by the lifespan handler.
app.state.media_service = build_media_service()

# Direct signed development byte transfer; production exposes metadata/signing only.
if get_settings().media_storage_backend == "local":
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["GET", "PUT"],
        allow_headers=["Content-Type"],
        expose_headers=["ETag"],
    )

    @app.put("/local-storage/{token}", include_in_schema=False)
    async def local_put(token: str, request: Request):
        import hashlib
        import json
        import os

        from app.storage import StorageError

        storage = service().storage
        try:
            body = storage.verify(token, "put")
        except StorageError:
            try:
                body = storage.verify(token, "part")
            except StorageError:
                return JSONResponse({"error": "invalid storage capability"}, status_code=403)
        path = storage.location(body["bucket"], body["key"])
        if body["action"] == "part":
            path = (
                storage.parts_path(body["bucket"], body["key"], body["upload_id"])
                / f"{int(body['part_number'])}.part"
            )
        elif request.headers.get("content-type") != body["mime"]:
            return JSONResponse({"error": "content type mismatch"}, status_code=400)
        temporary = path.with_suffix(".uploading")
        size = 0
        digest = hashlib.sha256()
        try:
            with temporary.open("wb") as handle:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 64 * 1024 * 1024:
                        return JSONResponse(
                            {"error": "local part limit is 64 MiB; use multipart"}, status_code=413
                        )
                    digest.update(chunk)
                    handle.write(chunk)
            os.replace(temporary, path)
            if body["action"] == "put":
                path.with_suffix(".json").write_text(json.dumps({"mime": body["mime"]}))
            return JSONResponse({"status": "uploaded"}, headers={"ETag": digest.hexdigest()})
        finally:
            temporary.unlink(missing_ok=True)

    @app.get("/local-storage/{token}", include_in_schema=False)
    async def local_get(token: str):
        from fastapi.responses import FileResponse

        from app.storage import StorageError

        storage = service().storage
        try:
            body = storage.verify(token, "get")
        except StorageError:
            return JSONResponse({"error": "invalid storage capability"}, status_code=403)
        metadata = await storage.head(body["bucket"], body["key"])
        if metadata is None:
            return JSONResponse({"error": "object unavailable"}, status_code=404)
        return FileResponse(
            storage.location(body["bucket"], body["key"]), media_type=metadata.mime_type
        )


def service() -> MediaService:
    return app.state.media_service


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready():
    from sqlalchemy import text

    try:
        if isinstance(service(), DurableMediaService):
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
        storage_ready = await service().storage.ready()
    except Exception:
        storage_ready = False
    if storage_ready:
        response = {"status": "ready", "storage": "available"}
        if isinstance(service(), DurableMediaService):
            response["database"] = "available"
        return response
    return JSONResponse(status_code=503, content={"status": "not_ready", "storage": "unavailable"})


@app.post("/api/v1/media/uploads", status_code=201)
async def initiate_upload(
    request: UploadRequest, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().initiate(
        principal, request, http_request.headers.get("X-Correlation-ID", "")
    )


@app.post("/api/v1/media/multipart", status_code=201)
async def initiate_multipart(
    request: UploadRequest, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().initiate_multipart(
        principal, request, http_request.headers.get("X-Correlation-ID", "")
    )


@app.post("/api/v1/media/{media_id}/multipart/parts")
async def multipart_parts(
    media_id: UUID,
    request: MultipartPartsRequest,
    principal: Principal = Depends(get_principal),
):
    return await service().multipart_part_urls(principal, media_id, request.part_numbers)


@app.get("/api/v1/media/{media_id}/multipart")
async def multipart_resume(media_id: UUID, principal: Principal = Depends(get_principal)):
    return await service().multipart_status(principal, media_id)


@app.post("/api/v1/media/{media_id}/multipart/complete")
async def complete_multipart(
    media_id: UUID,
    request: MultipartCompleteRequest,
    http_request: Request,
    principal: Principal = Depends(get_principal),
):
    return await service().complete_multipart(
        principal, media_id, request.parts, http_request.headers.get("X-Correlation-ID", "")
    )


@app.delete("/api/v1/media/{media_id}/multipart")
async def abort_multipart(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    await service().abort_multipart(
        principal, media_id, http_request.headers.get("X-Correlation-ID", "")
    )
    return {"status": "aborted"}


@app.post("/api/v1/media/{media_id}/complete")
async def complete_upload(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().complete(
        principal, media_id, http_request.headers.get("X-Correlation-ID", "")
    )


@app.get("/api/v1/media/{media_id}/download")
async def download(media_id: UUID, principal: Principal = Depends(get_principal)):
    return {"download_url": await service().download(principal, media_id)}


@app.delete("/api/v1/media/{media_id}")
async def delete(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    await service().delete(principal, media_id, http_request.headers.get("X-Correlation-ID", ""))
    return {"status": "deleted"}
