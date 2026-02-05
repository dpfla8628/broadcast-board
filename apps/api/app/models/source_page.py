# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class SourcePage(Base, TimestampMixin):
    """크롤링 대상 페이지 관리 테이블.

    - why: 소스를 코드로만 관리하면 운영 중에 끄기/켜기가 어렵기 때문에 DB로 관리.
    """

    __tablename__ = "source_pages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(100), index=True)
    page_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
