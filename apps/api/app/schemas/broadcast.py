# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from pydantic import BaseModel
from app.models.broadcast_slot import BroadcastStatus
from app.schemas.common import TimestampSchema


class BroadcastOut(TimestampSchema):
    """방송 슬롯 응답 스키마."""

    id: int
    channel_id: int
    channel_code: str | None = None
    channel_name: str | None = None
    source_code: str
    start_at: datetime
    end_at: datetime
    raw_title: str
    normalized_title: str
    category: str | None = None
    product_url: str | None = None
    live_url: str | None = None
    sale_price: int | None = None
    original_price: int | None = None
    discount_rate: float | None = None
    price_text: str | None = None
    image_url: str | None = None
    status: BroadcastStatus
    slot_hash: str

    class Config:
        from_attributes = True


class BroadcastDetailOut(BroadcastOut):
    """상세 응답 스키마. MVP에서는 BroadcastOut과 동일하지만 확장을 고려해 분리."""

    pass


class PriceHistoryOut(BaseModel):
    """가격 변동 이력 응답."""

    collected_at: datetime
    sale_price: int | None = None
    original_price: int | None = None
    discount_rate: float | None = None

    class Config:
        from_attributes = True
