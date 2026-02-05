# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import enum
from datetime import datetime
from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin


class BroadcastStatus(str, enum.Enum):
    """방송 상태.

    - 왜 Enum인가: 상태 값의 오타를 방지하고, 검색 조건을 안전하게 만들기 위해.
    """

    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    ENDED = "ENDED"


class BroadcastSlot(Base, TimestampMixin):
    """편성표 방송 슬롯.

    - 핵심 테이블이며, 슬롯 중복을 막기 위해 slot_hash 유니크를 사용.
    """

    __tablename__ = "broadcast_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    source_code: Mapped[str] = mapped_column(String(100))

    start_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime)

    raw_title: Mapped[str] = mapped_column(Text)
    # MySQL에서 인덱스가 가능하도록 길이를 제한한 문자열로 저장
    normalized_title: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    live_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sale_price: Mapped[int | None] = mapped_column(nullable=True)
    original_price: Mapped[int | None] = mapped_column(nullable=True)
    discount_rate: Mapped[float | None] = mapped_column(nullable=True)
    price_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name="broadcast_status"),
        default=BroadcastStatus.SCHEDULED,
        index=True,
    )

    slot_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    channel = relationship("Channel")

    @property
    def channel_code(self) -> str | None:
        # why: 응답에서 채널 코드가 바로 필요할 때 조인 결과를 노출
        if not self.channel:
            return None
        return self.channel.channel_code

    @property
    def channel_name(self) -> str | None:
        # why: 카드에 채널명을 표시하기 위해 조인 결과를 노출
        if not self.channel:
            return None
        return self.channel.channel_name


Index("idx_broadcast_channel_start", BroadcastSlot.channel_id, BroadcastSlot.start_at)
Index("idx_broadcast_start", BroadcastSlot.start_at)
Index("idx_broadcast_norm_title", BroadcastSlot.normalized_title)
Index("idx_broadcast_category", BroadcastSlot.category)
