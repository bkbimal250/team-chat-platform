from pydantic import BaseModel, ConfigDict


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    platform: str
    provider: str
    push_token: str


class PreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    push_enabled: bool | None = None
    message_notifications: bool | None = None
    group_notifications: bool | None = None
    notification_preview: str | None = None
    sound_enabled: bool | None = None
    vibration_enabled: bool | None = None
