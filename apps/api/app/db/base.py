# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 모델이 상속하는 SQLAlchemy Base.

    - 왜 별도 클래스인가: metadata를 중앙에서 관리하고 alembic 연동을 단순화하기 위해.
    """

    pass
