# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from pydantic import BaseModel, Field
from app.models.alert import DestinationType
from app.schemas.common import TimestampSchema


class AlertBase(BaseModel):
    """알림 공통 필드."""

    alert_name: str
    target_channel_codes: list[str]
    keyword_list: list[str]
    category_list: list[str] | None = None
    notify_before_minutes: int = Field(default=30, ge=0, le=1440)
    destination_type: DestinationType = DestinationType.SLACK
    destination_value: str
    is_active: bool = True


class AlertCreate(AlertBase):
    """알림 생성 요청 스키마."""

    pass


class AlertUpdate(BaseModel):
    """알림 수정 요청 스키마. PATCH라서 전부 optional."""

    alert_name: str | None = None
    target_channel_codes: list[str] | None = None
    keyword_list: list[str] | None = None
    category_list: list[str] | None = None
    notify_before_minutes: int | None = Field(default=None, ge=0, le=1440)
    destination_type: DestinationType | None = None
    destination_value: str | None = None
    is_active: bool | None = None


class AlertOut(AlertBase, TimestampSchema):
    """알림 응답 스키마."""

    id: int

    class Config:
        from_attributes = True
