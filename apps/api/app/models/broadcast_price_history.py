# why: 방송 가격 변동 이력을 저장하기 위한 모델
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BroadcastPriceHistory(Base):
    __tablename__ = "broadcast_price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    broadcast_slot_id: Mapped[int] = mapped_column(
        ForeignKey("broadcast_slots.id"), index=True
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sale_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
