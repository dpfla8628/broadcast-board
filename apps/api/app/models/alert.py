# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import enum
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.base import TimestampMixin


class DestinationType(str, enum.Enum):
    """알림 목적지 타입.

    - MVP에서는 SLACK만 사용하지만, 확장성을 위해 Enum으로 설계.
    """

    SLACK = "SLACK"
    EMAIL = "EMAIL"


class Alert(Base, TimestampMixin):
    """알림 규칙 테이블.

    - why: 키워드/채널/시간 조건을 저장해 배치가 조건에 맞는 방송을 찾아 알림 발송.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_name: Mapped[str] = mapped_column(String(100))

    target_channel_codes: Mapped[list[str]] = mapped_column(JSON)
    keyword_list: Mapped[list[str]] = mapped_column(JSON)
    category_list: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    notify_before_minutes: Mapped[int] = mapped_column(default=30)

    destination_type: Mapped[DestinationType] = mapped_column(
        Enum(DestinationType, name="destination_type"),
        default=DestinationType.SLACK,
    )
    destination_value: Mapped[str] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
