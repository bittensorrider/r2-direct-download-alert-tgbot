from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal["download", "object-create", "object-delete"]


class R2Event(BaseModel):
    event_type: EventType
    bucket: str
    key: str
    timestamp: str

    action: str | None = None
    size: int | None = None
    e_tag: str | None = Field(default=None, alias="eTag")

    method: str | None = None
    ip: str | None = None
    country: str | None = None
    user_agent: str | None = Field(default=None, alias="userAgent")
    referer: str | None = None
    range_header: str | None = Field(default=None, alias="range")
    bytes_sent: int | None = Field(default=None, alias="bytesSent")

    model_config = {"populate_by_name": True}


# Backward-compatible alias used by older worker configs.
class DownloadEvent(R2Event):
    event_type: EventType = "download"
