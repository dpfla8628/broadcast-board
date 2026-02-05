# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """생성/수정 시각 공통 믹스인.

    - why: 여러 테이블에서 동일한 컬럼을 반복하지 않기 위해.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
