# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from pydantic import BaseModel
from app.schemas.common import TimestampSchema


class ChannelOut(TimestampSchema):
    """채널 응답 스키마."""

    id: int
    channel_code: str
    channel_name: str
    channel_logo_url: str | None = None
    channel_live_url: str | None = None
    channel_stream_url: str | None = None

    class Config:
        from_attributes = True
