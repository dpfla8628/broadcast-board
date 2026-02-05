# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class BroadcastStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    ENDED = "ENDED"


class DestinationType(str, enum.Enum):
    SLACK = "SLACK"
    EMAIL = "EMAIL"


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    channel_name: Mapped[str] = mapped_column(String(100))
    channel_logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_live_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class BroadcastSlot(Base):
    __tablename__ = "broadcast_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    source_code: Mapped[str] = mapped_column(String(100))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    raw_title: Mapped[str] = mapped_column(Text)
    # MySQL 인덱스 제약을 고려해 길이를 제한한 문자열로 저장
    normalized_title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    live_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sale_price: Mapped[int | None] = mapped_column(nullable=True)
    original_price: Mapped[int | None] = mapped_column(nullable=True)
    discount_rate: Mapped[float | None] = mapped_column(nullable=True)
    price_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name="broadcast_status")
    )
    slot_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_name: Mapped[str] = mapped_column(String(100))
    target_channel_codes: Mapped[list[str]] = mapped_column(JSON)
    keyword_list: Mapped[list[str]] = mapped_column(JSON)
    category_list: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    notify_before_minutes: Mapped[int] = mapped_column()
    destination_type: Mapped[DestinationType] = mapped_column(
        Enum(DestinationType, name="destination_type")
    )
    destination_value: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean)


class BroadcastPriceHistory(Base):
    __tablename__ = "broadcast_price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    broadcast_slot_id: Mapped[int] = mapped_column(ForeignKey("broadcast_slots.id"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sale_price: Mapped[int | None] = mapped_column(nullable=True)
    original_price: Mapped[int | None] = mapped_column(nullable=True)
    discount_rate: Mapped[float | None] = mapped_column(nullable=True)
