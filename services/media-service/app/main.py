from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import MediaPolicy, MediaSettings, get_settings
from app.db import engine
from app.schemas import MultipartCompleteRequest, MultipartPartsRequest, UploadRequest
from app.security import Principal, get_principal
from app.service import MediaService
from app.storage import FakePrivateStorage, S3PrivateStorage


def build_media_service(settings: MediaSettings | None = None) -> MediaService:
    settings = settings or get_settings()
    if settings.media_storage_backend == "s3":
        storage = S3PrivateStorage(
            region=settings.aws_region,
            bucket=settings.media_s3_bucket,
            endpoint_url=settings.media_s3_endpoint_url,
        )
        bucket = settings.media_s3_bucket
    else:
        storage = FakePrivateStorage()
        bucket = settings.media_s3_bucket or "team-chat-platform-private"
    return MediaService(storage, MediaPolicy(bucket=bucket))


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


def service() -> MediaService:
    return app.state.media_service


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready():
    if await service().storage.ready():
        return {"status": "ready", "storage": "available"}
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
