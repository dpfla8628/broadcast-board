# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class Channel(Base, TimestampMixin):
    """홈쇼핑 채널 테이블.

    - why: 편성표와 알림의 기준 단위이므로 별도 엔티티로 분리.
    """

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    channel_name: Mapped[str] = mapped_column(String(100))
    channel_logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_live_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_stream_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
