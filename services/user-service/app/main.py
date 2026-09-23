import os
import uuid
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.auth import AuthContext, require_authenticated_context


class Base(DeclarativeBase):
    pass


def uid():
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200), default="")
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    about: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserBlock(Base):
    __tablename__ = "user_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_user_id", "blocked_user_id", name="user_block_unique"),
        CheckConstraint("blocker_user_id <> blocked_user_id", name="user_block_not_self"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    blocker_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    blocked_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    language: Mapped[str] = mapped_column(String(16), default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    theme_preference: Mapped[str] = mapped_column(String(16), default="SYSTEM")
    enter_to_send: Mapped[bool] = mapped_column(default=True)
    media_auto_download: Mapped[bool] = mapped_column(default=True)
    link_preview_enabled: Mapped[bool] = mapped_column(default=True)


class UserPrivacySettings(Base):
    __tablename__ = "user_privacy_settings"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    profile_photo_visibility: Mapped[str] = mapped_column(String(20), default="ORGANIZATION")
    about_visibility: Mapped[str] = mapped_column(String(20), default="ORGANIZATION")
    online_status_visibility: Mapped[str] = mapped_column(String(20), default="ORGANIZATION")
    last_seen_visibility: Mapped[str] = mapped_column(String(20), default="NOBODY")
    read_receipts_enabled: Mapped[bool] = mapped_column(default=True)


class MembershipProjection(Base):
    __tablename__ = "membership_projections"
    __table_args__ = (
        UniqueConstraint("organization_id", "member_id", name="membership_projection_unique"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20))


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    event_type: Mapped[str] = mapped_column(String(100))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    event_type: Mapped[str] = mapped_column(String(100))
    producer: Mapped[str] = mapped_column(String(80))
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


engine = create_async_engine(
    os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@127.0.0.1/teamchat_user_db")
)
sessions = async_sessionmaker(engine, expire_on_commit=False)
app = FastAPI(title="User Service", version="1.0.0")


async def db():
    async with sessions() as session:
        yield session


async def internal(x_internal_service_token: str = Header(...)):
    if x_internal_service_token != os.getenv("INTERNAL_SERVICE_TOKEN", ""):
        raise HTTPException(401, "service authentication required")


class BlockCheck(BaseModel):
    user_a_id: uuid.UUID
    user_b_id: uuid.UUID


class ProjectionRequest(BaseModel):
    user_ids: list[uuid.UUID] = Field(max_length=100)


class ProfilePatch(BaseModel):
    display_name: str | None = Field(None, max_length=200)
    avatar_media_id: uuid.UUID | None = None
    about: str | None = Field(None, max_length=2000)


class SettingsPatch(BaseModel):
    language: str | None = None
    timezone: str | None = None
    theme_preference: str | None = None
    enter_to_send: bool | None = None
    media_auto_download: bool | None = None
    link_preview_enabled: bool | None = None


class PrivacyPatch(BaseModel):
    profile_photo_visibility: str | None = None
    about_visibility: str | None = None
    online_status_visibility: str | None = None
    last_seen_visibility: str | None = None
    read_receipts_enabled: bool | None = None


async def current_user(session: AsyncSession, context: AuthContext) -> User:
    user = await session.scalar(select(User).where(User.identity_id == context.identity_id))
    if user is None:
        raise HTTPException(404, "user profile not provisioned")
    return user


def projection(user: User) -> dict:
    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "avatar_media_id": str(user.avatar_media_id) if user.avatar_media_id else None,
        "about": user.about,
        "status": user.status,
    }


def outbox(session: AsyncSession, user: User, event_type: str) -> None:
    session.add(
        OutboxEvent(
            event_type=event_type,
            aggregate_id=user.id,
            correlation_id="",
            payload={"user_id": str(user.id)},
            organization_id=None,
        )
    )


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.post("/internal/v1/users/block-check", dependencies=[Depends(internal)])
async def block_check(body: BlockCheck, session: AsyncSession = Depends(db)):
    q = select(UserBlock.id).where(
        (
            (UserBlock.blocker_user_id == body.user_a_id)
            & (UserBlock.blocked_user_id == body.user_b_id)
        )
        | (
            (UserBlock.blocker_user_id == body.user_b_id)
            & (UserBlock.blocked_user_id == body.user_a_id)
        )
    )
    return {"blocked": await session.scalar(q) is not None}


@app.post("/internal/v1/users/projections", dependencies=[Depends(internal)])
async def projections(body: ProjectionRequest, session: AsyncSession = Depends(db)):
    users = (await session.scalars(select(User).where(User.id.in_(body.user_ids)))).all()
    return {
        "users": [
            {
                "user_id": str(u.id),
                "display_name": u.display_name,
                "avatar_media_id": str(u.avatar_media_id) if u.avatar_media_id else None,
                "status": u.status,
            }
            for u in users
        ]
    }


@app.get("/api/v1/users/me")
async def me(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    return projection(await current_user(session, context))


@app.patch("/api/v1/users/me")
async def update_me(
    body: ProfilePatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        outbox(session, user, "user.profile_updated.v1")
    return projection(user)


@app.get("/api/v1/users/me/preferences")
async def preferences(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    value = await session.get(UserPreferences, user.id)
    if not value:
        raise HTTPException(404, "preferences not provisioned")
    return {key: getattr(value, key) for key in SettingsPatch.model_fields}


@app.patch("/api/v1/users/me/preferences")
async def update_preferences(
    body: SettingsPatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        value = await session.get(UserPreferences, user.id)
        if not value:
            value = UserPreferences(user_id=user.id)
            session.add(value)
        for key, item in body.model_dump(exclude_unset=True).items():
            setattr(value, key, item)
        outbox(session, user, "user.preferences_updated.v1")
    return {key: getattr(value, key) for key in SettingsPatch.model_fields}


@app.post("/api/v1/users/{user_id}/block")
async def block(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        if user.id == user_id:
            raise HTTPException(422, "cannot block yourself")
        item = await session.scalar(
            select(UserBlock).where(
                UserBlock.blocker_user_id == user.id, UserBlock.blocked_user_id == user_id
            )
        )
        if not item:
            session.add(UserBlock(blocker_user_id=user.id, blocked_user_id=user_id))
            outbox(session, user, "user.blocked.v1")
    return {"blocked": True}


@app.delete("/api/v1/users/{user_id}/block")
async def unblock(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        item = await session.scalar(
            select(UserBlock).where(
                UserBlock.blocker_user_id == user.id, UserBlock.blocked_user_id == user_id
            )
        )
        if item:
            await session.delete(item)
            outbox(session, user, "user.unblocked.v1")
    return {"blocked": False}


@app.get("/api/v1/users/me/privacy")
async def privacy(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    value = await session.get(UserPrivacySettings, user.id)
    if value is None:
        raise HTTPException(404, "privacy settings not provisioned")
    return {key: getattr(value, key) for key in PrivacyPatch.model_fields}


@app.patch("/api/v1/users/me/privacy")
async def update_privacy(
    body: PrivacyPatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    allowed = {"EVERYONE", "ORGANIZATION", "CONTACTS", "NOBODY"}
    async with session.begin():
        user = await current_user(session, context)
        value = await session.get(UserPrivacySettings, user.id)
        if value is None:
            value = UserPrivacySettings(user_id=user.id)
            session.add(value)
        for key, item in body.model_dump(exclude_unset=True).items():
            if key.endswith("visibility") and item not in allowed:
                raise HTTPException(422, "invalid visibility")
            setattr(value, key, item)
        outbox(session, user, "user.privacy_updated.v1")
    return {key: getattr(value, key) for key in PrivacyPatch.model_fields}


@app.get("/api/v1/users/me/blocked")
async def blocked_users(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    rows = await session.scalars(
        select(User)
        .join(UserBlock, UserBlock.blocked_user_id == User.id)
        .where(UserBlock.blocker_user_id == user.id)
    )
    return {"users": [projection(item) for item in rows]}


@app.get("/api/v1/users/search")
async def search_users(
    q: str = "",
    limit: int = 20,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    if len(q.strip()) < 2:
        raise HTTPException(422, "query must contain at least two characters")
    limit = min(max(limit, 1), 50)
    query = (
        select(User)
        .join(MembershipProjection, MembershipProjection.user_id == User.id)
        .where(
            MembershipProjection.organization_id == context.organization_id,
            MembershipProjection.status == "ACTIVE",
            User.display_name.ilike(f"%{q.strip()}%"),
        )
        .limit(limit)
    )
    return {"users": [projection(item) for item in (await session.scalars(query)).all()]}


@app.get("/api/v1/users/{user_id}")
async def get_profile(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(404, "user not found")
    if target.identity_id != context.identity_id:
        visible = await session.scalar(
            select(MembershipProjection.id).where(
                MembershipProjection.organization_id == context.organization_id,
                MembershipProjection.user_id == target.id,
                MembershipProjection.status == "ACTIVE",
            )
        )
        if visible is None:
            raise HTTPException(404, "user not found")
    return projection(target)
