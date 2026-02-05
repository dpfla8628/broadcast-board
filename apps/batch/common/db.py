# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import get_batch_settings


settings = get_batch_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session():
    """배치 전용 세션 팩토리."""

    return SessionLocal()
