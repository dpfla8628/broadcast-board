# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


settings = get_settings()

# MySQL은 기본적으로 자동 커밋이 없으므로, 명시적 커밋/롤백 흐름을 사용.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """요청 단위 DB 세션 의존성.

    - why: FastAPI의 Depends로 세션 생명주기를 통일.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
