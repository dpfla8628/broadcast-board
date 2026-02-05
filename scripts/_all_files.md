README.md
```md
# BroadcastBoard

홈쇼핑 편성표를 배치로 수집하고, API/대시보드로 관리하는 모노레포 MVP입니다.

## 핵심 기능
- 편성표 배치 수집 → MySQL 적재
- FastAPI로 편성표/채널/알림 CRUD
- Next.js 대시보드에서 타임라인/상세/알림 관리
- Slack 웹훅 알림 발송(최소 구현)

## 아키텍처 개요
- `apps/batch`: 크롤링 배치 (Fetcher → Parser → Normalizer → Upsert → Logging)
- `apps/api`: FastAPI + SQLAlchemy API 서버
- `apps/web`: Next.js(React) 대시보드
- `scripts`: 로컬 DB 세팅/실행 문서

## 데이터 흐름
1. 배치가 편성표 페이지를 크롤링
2. 파서가 슬롯 리스트로 변환
3. 정규화/해시 생성 → 중복 방지 업서트
4. API가 MySQL에서 슬롯/알림/채널 조회
5. 웹 대시보드가 API 호출로 화면 표시
6. 배치가 알림 규칙과 편성표를 매칭해 Slack 발송

## 시간대 정책
- DB에는 UTC로 저장합니다.
- API 응답은 ISO8601 UTC입니다.
- 프론트에서 KST로 변환해 표시하는 것을 기본 가정으로 합니다.

## 로컬 실행
- `scripts/setup_local_mysql.md`
- `scripts/run_local.md`

## 폴더 설명
- `apps/api/app`: FastAPI 본체 (routes → services → repositories → models)
- `apps/api/alembic`: 마이그레이션 관리
- `apps/batch`: 배치 파이프라인
- `apps/web`: Next.js UI
- `scripts`: 로컬 실행 문서

## 보안
- `.env` 파일은 커밋하지 않습니다.
- 제공된 `.env.example` 파일을 복사해 사용하세요.
```

scripts/setup_local_mysql.md
```md
# 로컬 MySQL 설치/세팅 가이드

## macOS (Homebrew)
1. 설치
   - `brew install mysql@8.0`
2. 서비스 실행
   - `brew services start mysql@8.0`
3. 접속
   - `mysql -u root`

## Ubuntu/Debian
1. 설치
   - `sudo apt update`
   - `sudo apt install mysql-server`
2. 서비스 실행
   - `sudo systemctl start mysql`
3. 접속
   - `sudo mysql`

## Windows (WSL2)
1. WSL2 Ubuntu 설치 후 아래 명령 실행
   - `sudo apt update`
   - `sudo apt install mysql-server`
   - `sudo service mysql start`
2. 접속
   - `sudo mysql`

## DB 생성 및 계정 설정
```sql
CREATE DATABASE nkshop_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nkshop_user'@'%' IDENTIFIED BY 'nkshop_password_1234';
GRANT ALL PRIVILEGES ON nkshop_local.* TO 'nkshop_user'@'%';
FLUSH PRIVILEGES;
```

## 접속 테스트
- `mysql -u nkshop_user -p -h 127.0.0.1 -P 3306 nkshop_local`
```

scripts/run_local.md
```md
# 로컬 실행 순서

1. DB 세팅
   - `scripts/setup_local_mysql.md` 참고

2. API 마이그레이션
   - `cd apps/api`
   - `alembic upgrade head`

3. 배치 실행 (편성표 수집)
   - `cd apps/batch`
   - `python -m batch.main fetch_schedule`

4. API 실행
   - `cd apps/api`
   - `uvicorn app.main:app --reload --port 8000`

5. 웹 실행
   - `cd apps/web`
   - `npm install`
   - `npm run dev`
```

apps/api/.env.example
```
# API 환경 변수 예시 (실제 .env는 커밋 금지)
APP_ENV=local
DATABASE_URL=mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local
CORS_ORIGINS=["http://localhost:3000"]
API_HOST=0.0.0.0
API_PORT=8000
TIME_POLICY=UTC
```

apps/api/alembic/env.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# app 패키지 경로 추가 (alembic 실행 위치 기준)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import get_settings
from app.db.base import Base
from app import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

apps/api/alembic/versions/0001_init.py
```python
"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
# noqa: RUF012
# alembic requires these module-level variables
# (자동 생성 규칙을 따르기 위해 명시적으로 유지)
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("channel_name", sa.String(length=100), nullable=False),
        sa.Column("channel_logo_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_channels_channel_code", "channels", ["channel_code"])

    op.create_table(
        "source_pages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_code", sa.String(length=100), nullable=False),
        sa.Column("page_url", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_source_pages_source_code", "source_pages", ["source_code"])

    op.create_table(
        "broadcast_slots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("source_code", sa.String(length=100), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("raw_title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("product_url", sa.String(length=500), nullable=True),
        sa.Column("price_text", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            sa.Enum("SCHEDULED", "LIVE", "ENDED", name="broadcast_status"),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("slot_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
    )
    op.create_unique_constraint("uq_broadcast_slots_slot_hash", "broadcast_slots", ["slot_hash"])
    op.create_index("ix_broadcast_slots_channel_id", "broadcast_slots", ["channel_id"])
    op.create_index("ix_broadcast_slots_start_at", "broadcast_slots", ["start_at"])
    op.create_index("ix_broadcast_slots_normalized_title", "broadcast_slots", ["normalized_title"])
    op.create_index(
        "idx_broadcast_channel_start", "broadcast_slots", ["channel_id", "start_at"]
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("alert_name", sa.String(length=100), nullable=False),
        sa.Column("target_channel_codes", sa.JSON(), nullable=False),
        sa.Column("keyword_list", sa.JSON(), nullable=False),
        sa.Column("category_list", sa.JSON(), nullable=True),
        sa.Column("notify_before_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column(
            "destination_type",
            sa.Enum("SLACK", "EMAIL", name="destination_type"),
            server_default="SLACK",
            nullable=False,
        ),
        sa.Column("destination_value", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("broadcast_slots")
    op.drop_table("source_pages")
    op.drop_table("channels")
```

apps/api/alembic.ini
```ini
[alembic]
script_location = alembic
sqlalchemy.url = mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

apps/api/app/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/core/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/core/config.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from functools import lru_cache
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정을 환경변수에서 읽어오는 클래스.

    - 왜 BaseSettings를 쓰나: 실행 환경마다 다른 값을 안전하게 주입하기 위해서.
    - env 파일을 직접 로드하는 대신, pydantic-settings 표준을 활용해 일관성을 유지.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "BroadcastBoard API"
    app_env: str = Field(default="local", description="dev|staging|prod")
    database_url: str = Field(
        default="mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local",
        description="SQLAlchemy 접속 문자열",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="허용할 프론트엔드 오리진",
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # API 응답의 시간대 정책을 명시적으로 노출하기 위해 사용
    time_policy: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

apps/api/app/core/errors.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import HTTPException


class AppError(HTTPException):
    """공통 에러 클래스.

    - why: 에러 포맷을 통일하기 위해 HTTPException을 상속.
    """

    def __init__(self, status_code: int, message: str, code: str = "APP_ERROR"):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
```

apps/api/app/core/utils.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import hashlib
from datetime import datetime


def make_slot_hash(channel_id: int, start_at: datetime, normalized_title: str) -> str:
    """방송 슬롯 고유 해시 생성.

    - 왜 해시를 쓰나: (채널+시작시간+정규화 제목) 조합이 사실상 유일하지만,
      인덱스 길이와 저장 비용을 줄이기 위해 고정 길이 해시를 사용.
    """

    base = f"{channel_id}|{start_at.isoformat()}|{normalized_title}".lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
```

apps/api/app/db/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/db/base.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """모든 모델이 상속하는 SQLAlchemy Base.

    - 왜 별도 클래스인가: metadata를 중앙에서 관리하고 alembic 연동을 단순화하기 위해.
    """

    pass
```

apps/api/app/db/session.py
```python
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
```

apps/api/app/main.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.routes.alert_routes import router as alert_router
from app.routes.broadcast_routes import router as broadcast_router
from app.routes.channel_routes import router as channel_router


settings = get_settings()

app = FastAPI(title=settings.app_name)

# CORS는 로컬 개발 환경에서 프론트와 API가 포트를 달리 사용하는 문제를 해결하기 위해 필요.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 모든 커스텀 에러를 동일한 구조로 반환해 프론트 처리 단순화
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "meta": {
                "message": exc.detail.get("message"),
                "code": exc.detail.get("code"),
                "time_policy": settings.time_policy,
            },
        },
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "data": None,
            "meta": {
                "message": "요청 값이 올바르지 않습니다.",
                "code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "time_policy": settings.time_policy,
            },
        },
    )


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    # FastAPI 기본 예외도 동일 포맷으로 감싸 프론트 로직을 단순화
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "meta": {
                "message": str(exc.detail),
                "code": "HTTP_EXCEPTION",
                "time_policy": settings.time_policy,
            },
        },
    )


@app.get("/api/v1/health")
def health_check():
    return {"data": {"status": "ok"}, "meta": {"time_policy": settings.time_policy}}


app.include_router(channel_router)
app.include_router(broadcast_router)
app.include_router(alert_router)
```

apps/api/app/models/__init__.py
```python
# why: 모델 심볼을 한 곳에서 노출해 import 경로를 단순화하기 위한 모듈
from app.models.alert import Alert, DestinationType
from app.models.broadcast_slot import BroadcastSlot, BroadcastStatus
from app.models.channel import Channel
from app.models.source_page import SourcePage

__all__ = [
    "Alert",
    "DestinationType",
    "BroadcastSlot",
    "BroadcastStatus",
    "Channel",
    "SourcePage",
]
```

apps/api/app/models/alert.py
```python
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
```

apps/api/app/models/base.py
```python
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
```

apps/api/app/models/broadcast_slot.py
```python
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
    normalized_title: Mapped[str] = mapped_column(Text, index=True)

    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[BroadcastStatus] = mapped_column(
        Enum(BroadcastStatus, name="broadcast_status"),
        default=BroadcastStatus.SCHEDULED,
        index=True,
    )

    slot_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    channel = relationship("Channel")


Index("idx_broadcast_channel_start", BroadcastSlot.channel_id, BroadcastSlot.start_at)
Index("idx_broadcast_start", BroadcastSlot.start_at)
Index("idx_broadcast_norm_title", BroadcastSlot.normalized_title)
```

apps/api/app/models/channel.py
```python
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
```

apps/api/app/models/source_page.py
```python
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
```

apps/api/app/repositories/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/repositories/alert_repo.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertRepository:
    """알림 규칙 데이터 접근 계층."""

    def list_alerts(self, db: Session) -> list[Alert]:
        return db.query(Alert).order_by(Alert.created_at.desc()).all()

    def get_alert(self, db: Session, alert_id: int) -> Alert | None:
        return db.query(Alert).filter(Alert.id == alert_id).first()

    def create_alert(self, db: Session, payload: AlertCreate) -> Alert:
        alert = Alert(**payload.model_dump())
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def update_alert(self, db: Session, alert: Alert, payload: AlertUpdate) -> Alert:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(alert, key, value)
        db.commit()
        db.refresh(alert)
        return alert

    def delete_alert(self, db: Session, alert: Alert) -> None:
        db.delete(alert)
        db.commit()
```

apps/api/app/repositories/broadcast_repo.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import date, datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.broadcast_slot import BroadcastSlot, BroadcastStatus


class BroadcastRepository:
    """방송 슬롯 데이터 접근 계층."""

    def list_broadcasts(
        self,
        db: Session,
        target_date: date | None = None,
        channel_code: str | None = None,
        keyword: str | None = None,
        status: BroadcastStatus | None = None,
    ) -> list[BroadcastSlot]:
        query = db.query(BroadcastSlot)

        if channel_code:
            # 채널 코드는 Channel 테이블을 조인해 필터링
            from app.models.channel import Channel

            query = query.join(Channel).filter(Channel.channel_code == channel_code)

        if keyword:
            query = query.filter(BroadcastSlot.normalized_title.ilike(f"%{keyword}%"))

        if status:
            query = query.filter(BroadcastSlot.status == status)

        if target_date:
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            query = query.filter(
                and_(BroadcastSlot.start_at >= start_dt, BroadcastSlot.start_at < end_dt)
            )

        return query.order_by(BroadcastSlot.start_at.asc()).all()

    def get_broadcast(self, db: Session, broadcast_id: int) -> BroadcastSlot | None:
        return db.query(BroadcastSlot).filter(BroadcastSlot.id == broadcast_id).first()
```

apps/api/app/repositories/channel_repo.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.models.channel import Channel


class ChannelRepository:
    """채널 데이터 접근 계층.

    - why: 서비스 계층에서 SQLAlchemy 세부 구현을 숨기기 위해.
    """

    def list_channels(self, db: Session) -> list[Channel]:
        return db.query(Channel).order_by(Channel.channel_name.asc()).all()
```

apps/api/app/routes/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/routes/alert_routes.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate
from app.schemas.common import ApiResponse, ResponseMeta
from app.services.alert_service import AlertService


router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])
service = AlertService()
settings = get_settings()


@router.get("", response_model=ApiResponse[list[AlertOut]])
def list_alerts(db: Session = Depends(get_db)):
    alerts = service.list_alerts(db)
    return ApiResponse(
        data=alerts,
        meta=ResponseMeta(count=len(alerts), time_policy=settings.time_policy),
    )


@router.post("", response_model=ApiResponse[AlertOut])
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    alert = service.create_alert(db, payload)
    return ApiResponse(
        data=alert,
        meta=ResponseMeta(message="created", time_policy=settings.time_policy),
    )


@router.patch("/{alert_id}", response_model=ApiResponse[AlertOut])
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)):
    alert = service.update_alert(db, alert_id, payload)
    return ApiResponse(
        data=alert,
        meta=ResponseMeta(message="updated", time_policy=settings.time_policy),
    )


@router.delete("/{alert_id}", response_model=ApiResponse[dict])
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    service.delete_alert(db, alert_id)
    return ApiResponse(
        data={"deleted": True},
        meta=ResponseMeta(message="deleted", time_policy=settings.time_policy),
    )
```

apps/api/app/routes/broadcast_routes.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.broadcast_slot import BroadcastStatus
from app.schemas.broadcast import BroadcastDetailOut, BroadcastOut
from app.schemas.common import ApiResponse, ResponseMeta
from app.services.broadcast_service import BroadcastService


router = APIRouter(prefix="/api/v1/broadcasts", tags=["broadcasts"])
service = BroadcastService()
settings = get_settings()


@router.get("", response_model=ApiResponse[list[BroadcastOut]])
def list_broadcasts(
    date_param: date | None = Query(default=None, alias="date"),
    channel_code: str | None = Query(default=None, alias="channelCode"),
    keyword: str | None = Query(default=None),
    status: BroadcastStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    broadcasts = service.list_broadcasts(db, date_param, channel_code, keyword, status)
    return ApiResponse(
        data=broadcasts,
        meta=ResponseMeta(count=len(broadcasts), time_policy=settings.time_policy),
    )


@router.get("/{broadcast_id}", response_model=ApiResponse[BroadcastDetailOut])
def get_broadcast(broadcast_id: int, db: Session = Depends(get_db)):
    broadcast = service.get_broadcast(db, broadcast_id)
    return ApiResponse(
        data=broadcast,
        meta=ResponseMeta(time_policy=settings.time_policy),
    )
```

apps/api/app/routes/channel_routes.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.channel import ChannelOut
from app.schemas.common import ApiResponse, ResponseMeta
from app.services.channel_service import ChannelService


router = APIRouter(prefix="/api/v1/channels", tags=["channels"])
service = ChannelService()
settings = get_settings()


@router.get("", response_model=ApiResponse[list[ChannelOut]])
def list_channels(db: Session = Depends(get_db)):
    channels = service.list_channels(db)
    return ApiResponse(
        data=channels,
        meta=ResponseMeta(count=len(channels), time_policy=settings.time_policy),
    )
```

apps/api/app/schemas/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/schemas/alert.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from pydantic import BaseModel, Field
from app.models.alert import DestinationType
from app.schemas.common import TimestampSchema


class AlertBase(BaseModel):
    """알림 공통 필드."""

    alert_name: str
    target_channel_codes: list[str]
    keyword_list: list[str]
    category_list: list[str] | None = None
    notify_before_minutes: int = Field(default=30, ge=0, le=1440)
    destination_type: DestinationType = DestinationType.SLACK
    destination_value: str
    is_active: bool = True


class AlertCreate(AlertBase):
    """알림 생성 요청 스키마."""

    pass


class AlertUpdate(BaseModel):
    """알림 수정 요청 스키마. PATCH라서 전부 optional."""

    alert_name: str | None = None
    target_channel_codes: list[str] | None = None
    keyword_list: list[str] | None = None
    category_list: list[str] | None = None
    notify_before_minutes: int | None = Field(default=None, ge=0, le=1440)
    destination_type: DestinationType | None = None
    destination_value: str | None = None
    is_active: bool | None = None


class AlertOut(AlertBase, TimestampSchema):
    """알림 응답 스키마."""

    id: int

    class Config:
        from_attributes = True
```

apps/api/app/schemas/broadcast.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from pydantic import BaseModel
from app.models.broadcast_slot import BroadcastStatus
from app.schemas.common import TimestampSchema


class BroadcastOut(TimestampSchema):
    """방송 슬롯 응답 스키마."""

    id: int
    channel_id: int
    source_code: str
    start_at: datetime
    end_at: datetime
    raw_title: str
    normalized_title: str
    product_url: str | None = None
    price_text: str | None = None
    image_url: str | None = None
    status: BroadcastStatus
    slot_hash: str

    class Config:
        from_attributes = True


class BroadcastDetailOut(BroadcastOut):
    """상세 응답 스키마. MVP에서는 BroadcastOut과 동일하지만 확장을 고려해 분리."""

    pass
```

apps/api/app/schemas/channel.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from pydantic import BaseModel
from app.schemas.common import TimestampSchema


class ChannelOut(TimestampSchema):
    """채널 응답 스키마."""

    id: int
    channel_code: str
    channel_name: str
    channel_logo_url: str | None = None

    class Config:
        from_attributes = True
```

apps/api/app/schemas/common.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class ResponseMeta(BaseModel):
    """응답 메타 정보.

    - 왜 분리했나: 목록 응답의 count, 메시지 등을 일관되게 담기 위해.
    """

    count: int | None = None
    message: str | None = None
    time_policy: str | None = None
    details: list[dict] | None = None


class ApiResponse(BaseModel, Generic[T]):
    """모든 API 응답을 감싸는 표준 포맷.

    - data/meta를 고정하면 프론트가 예외 없이 처리 가능.
    """

    data: T
    meta: ResponseMeta


class TimestampSchema(BaseModel):
    """created/updated 시각 공통 스키마."""

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

apps/api/app/services/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/api/app/services/alert_service.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertService:
    """알림 규칙 서비스 계층."""

    def __init__(self) -> None:
        self.repo = AlertRepository()

    def list_alerts(self, db: Session):
        return self.repo.list_alerts(db)

    def create_alert(self, db: Session, payload: AlertCreate):
        return self.repo.create_alert(db, payload)

    def update_alert(self, db: Session, alert_id: int, payload: AlertUpdate):
        alert = self.repo.get_alert(db, alert_id)
        if not alert:
            raise AppError(status_code=404, message="알림 규칙을 찾을 수 없습니다.", code="NOT_FOUND")
        return self.repo.update_alert(db, alert, payload)

    def delete_alert(self, db: Session, alert_id: int):
        alert = self.repo.get_alert(db, alert_id)
        if not alert:
            raise AppError(status_code=404, message="알림 규칙을 찾을 수 없습니다.", code="NOT_FOUND")
        self.repo.delete_alert(db, alert)
        return True
```

apps/api/app/services/broadcast_service.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import date
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.broadcast_slot import BroadcastStatus
from app.repositories.broadcast_repo import BroadcastRepository


class BroadcastService:
    """방송 슬롯 서비스 계층."""

    def __init__(self) -> None:
        self.repo = BroadcastRepository()

    def list_broadcasts(
        self,
        db: Session,
        target_date: date | None,
        channel_code: str | None,
        keyword: str | None,
        status: BroadcastStatus | None,
    ):
        return self.repo.list_broadcasts(db, target_date, channel_code, keyword, status)

    def get_broadcast(self, db: Session, broadcast_id: int):
        broadcast = self.repo.get_broadcast(db, broadcast_id)
        if not broadcast:
            raise AppError(status_code=404, message="방송 정보를 찾을 수 없습니다.", code="NOT_FOUND")
        return broadcast
```

apps/api/app/services/channel_service.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.repositories.channel_repo import ChannelRepository


class ChannelService:
    """채널 서비스 계층."""

    def __init__(self) -> None:
        self.repo = ChannelRepository()

    def list_channels(self, db: Session):
        return self.repo.list_channels(db)
```

apps/api/requirements.txt
```
fastapi==0.115.5
uvicorn==0.30.6
gunicorn==23.0.0
SQLAlchemy==2.0.36
alembic==1.14.0
pydantic==2.9.2
pydantic-settings==2.5.2
pymysql==1.1.1
python-dotenv==1.0.1
pytest==8.3.3
```

apps/api/tests/test_slot_hash.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from app.core.utils import make_slot_hash


def test_make_slot_hash_is_deterministic():
    # 같은 입력이면 항상 같은 해시가 나와야 중복 방지가 가능
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    hash2 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    assert hash1 == hash2


def test_make_slot_hash_changes_by_title():
    # 제목이 달라지면 다른 슬롯으로 간주해야 하므로 해시도 달라져야 함
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    hash2 = make_slot_hash(1, start_at, "프리미엄 침구 세트 2")
    assert hash1 != hash2
```

apps/batch/.env.example
```
# Batch 환경 변수 예시
DATABASE_URL=mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local
SCHEDULE_SOURCE_URL=https://example.com/gmarket/schedule
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook
USER_AGENT=BroadcastBoardBatch/1.0 (+https://local)
```

apps/batch/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/batch/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/batch/main.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import argparse
import logging

from batch.jobs.fetch_schedule_job import fetch_schedule_job
from batch.jobs.send_alerts_job import send_alerts_job


def setup_logging():
    # why: 배치 로그는 실패 원인과 수집 통계를 남겨야 하므로 간단한 표준 포맷 사용
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="BroadcastBoard Batch Runner")
    parser.add_argument(
        "job",
        choices=["fetch_schedule", "send_alerts"],
        help="실행할 배치 작업 이름",
    )
    args = parser.parse_args()

    if args.job == "fetch_schedule":
        fetch_schedule_job()
    elif args.job == "send_alerts":
        send_alerts_job()


if __name__ == "__main__":
    main()
```

apps/batch/common/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/common/config.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BatchSettings(BaseSettings):
    """배치 실행 설정.

    - why: 크롤링 URL, 슬랙 웹훅 등 환경 별로 달라지는 값을 안전하게 관리.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(
        default="mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local"
    )
    schedule_source_url: str = Field(
        default="https://example.com/gmarket/schedule",
        description="MVP에서 가정하는 편성표 페이지 URL",
    )
    slack_webhook_url: str | None = None
    user_agent: str = "BroadcastBoardBatch/1.0 (+https://local)"


@lru_cache
def get_batch_settings() -> BatchSettings:
    return BatchSettings()
```

apps/batch/common/db.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from batch.common.config import get_batch_settings


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
```

apps/batch/common/models.py
```python
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


class BroadcastSlot(Base):
    __tablename__ = "broadcast_slots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), index=True)
    source_code: Mapped[str] = mapped_column(String(100))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime] = mapped_column(DateTime)
    raw_title: Mapped[str] = mapped_column(Text)
    normalized_title: Mapped[str] = mapped_column(Text)
    product_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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
```

apps/batch/common/normalize.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import hashlib
import re
from datetime import datetime


UNWANTED_KEYWORDS = [
    "무료배송",
    "단독",
    "특가",
    "방송중",
    "오늘만",
    "기획전",
]


def normalize_product_title(raw_title: str) -> str:
    """상품명 정규화.

    - why: 서로 다른 표기(특수문자/이모지/불필요 키워드)가 있어도 같은 상품으로 인식해야
      슬롯 중복을 막고 검색 경험을 개선할 수 있음.
    """

    if not raw_title:
        return ""

    title = raw_title
    for keyword in UNWANTED_KEYWORDS:
        title = title.replace(keyword, "")

    # 특수문자를 공백으로 치환해 단어 단위 비교가 가능하도록 처리
    title = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", title)
    # 연속 공백은 하나로 줄여 비교/검색을 안정화
    title = re.sub(r"\s+", " ", title)

    return title.strip().lower()


def parse_price_text(price_text: str | None) -> int | None:
    """가격 문자열에서 정수만 추출.

    - why: '12,900원' 같은 표기를 숫자로 변환해 차트나 필터에 활용하기 위해.
    """

    if not price_text:
        return None

    digits = re.findall(r"\d+", price_text)
    if not digits:
        return None

    return int("".join(digits))


def make_slot_hash(channel_id: int, start_at: datetime, normalized_title: str) -> str:
    """슬롯 중복 방지를 위한 해시."""

    base = f"{channel_id}|{start_at.isoformat()}|{normalized_title}".lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
```

apps/batch/common/slack.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import httpx


def send_slack_message(webhook_url: str, text: str) -> None:
    """슬랙 웹훅으로 메시지 발송.

    - why: MVP의 알림 채널을 단순화하기 위해 webhook 방식 사용.
    """

    if not webhook_url:
        raise ValueError("Slack webhook URL이 비어 있습니다.")

    with httpx.Client(timeout=10.0) as client:
        response = client.post(webhook_url, json={"text": text})
        response.raise_for_status()
```

apps/batch/jobs/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/jobs/fetch_schedule_job.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import logging

from batch.common.db import get_db_session
from batch.pipelines.schedule_pipeline import run_schedule_pipeline


logger = logging.getLogger("batch.fetch")


def fetch_schedule_job():
    """편성표 수집 잡."""

    db = get_db_session()
    try:
        run_schedule_pipeline(db)
    finally:
        db.close()
```

apps/batch/jobs/send_alerts_job.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime, timedelta
import logging

from sqlalchemy import select

from batch.common.config import get_batch_settings
from batch.common.db import get_db_session
from batch.common.models import Alert, BroadcastSlot, Channel, DestinationType
from batch.common.slack import send_slack_message


logger = logging.getLogger("batch.alerts")


def _match_keywords(title: str, keywords: list[str]) -> bool:
    # why: 키워드 매칭을 단순화하여 빠른 MVP 구현을 보장
    lowered = title.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def send_alerts_job():
    """알림 발송 잡.

    - 오늘 편성표 중 키워드 매칭 & 시작 전 N분 조건을 만족하면 Slack으로 발송.
    """

    settings = get_batch_settings()
    db = get_db_session()

    now = datetime.utcnow()

    try:
        alerts = db.execute(select(Alert).where(Alert.is_active == True)).scalars().all()
        sent_count = 0

        for alert in alerts:
            if alert.destination_type != DestinationType.SLACK:
                continue
            if not alert.destination_value:
                continue

            window_end = now + timedelta(minutes=alert.notify_before_minutes)

            # 채널 조건
            channel_ids = db.execute(
                select(Channel.id).where(Channel.channel_code.in_(alert.target_channel_codes))
            ).scalars().all()

            if not channel_ids:
                continue

            broadcasts = (
                db.execute(
                    select(BroadcastSlot)
                    .where(BroadcastSlot.channel_id.in_(channel_ids))
                    .where(BroadcastSlot.start_at >= now)
                    .where(BroadcastSlot.start_at <= window_end)
                )
                .scalars()
                .all()
            )

            for broadcast in broadcasts:
                if not _match_keywords(broadcast.normalized_title, alert.keyword_list):
                    continue

                message = (
                    f"[{alert.alert_name}] 곧 시작하는 방송: {broadcast.raw_title}\n"
                    f"시작: {broadcast.start_at.isoformat()} (UTC)\n"
                    f"가격: {broadcast.price_text or '정보없음'}"
                )
                send_slack_message(alert.destination_value, message)
                sent_count += 1

        logger.info("알림 발송 완료. sent=%s", sent_count)
    finally:
        db.close()
```

apps/batch/parsers/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/parsers/gmarket_schedule_parser.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def parse_schedule(html: str) -> list[dict]:
    """가상의 gmarket 편성표 HTML 파서.

    - why: 실제 HTML은 변할 수 있으므로, 파서 결과를 표준 dict로 만들어 파이프라인을 안정화.
    - 반환 값 예시:
      {
        "start_at": datetime,
        "end_at": datetime,
        "raw_title": "...",
        "price_text": "12,900원",
        "image_url": "...",
        "product_url": "...",
      }
    """

    soup = BeautifulSoup(html, "html.parser")
    items = []

    # 예시 구조: <div class="schedule-item" data-start="09:00" data-end="10:00">
    for node in soup.select(".schedule-item"):
        start_text = node.get("data-start", "")
        end_text = node.get("data-end", "")
        title = (node.select_one(".title") or node).get_text(strip=True)
        price = (node.select_one(".price") or node).get_text(strip=True)
        image = None
        link = None

        img_tag = node.select_one("img")
        if img_tag:
            image = img_tag.get("src")

        a_tag = node.select_one("a")
        if a_tag:
            link = a_tag.get("href")

        # 시간 정보가 없으면 파싱 실패로 간주하고 스킵
        if not start_text:
            continue

        today = datetime.utcnow().date()
        start_at = datetime.strptime(f"{today} {start_text}", "%Y-%m-%d %H:%M")
        if end_text:
            end_at = datetime.strptime(f"{today} {end_text}", "%Y-%m-%d %H:%M")
        else:
            end_at = start_at + timedelta(hours=1)

        items.append(
            {
                "start_at": start_at,
                "end_at": end_at,
                "raw_title": title,
                "price_text": price,
                "image_url": image,
                "product_url": link,
            }
        )

    return items
```

apps/batch/pipelines/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/pipelines/schedule_pipeline.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from batch.common.models import BroadcastSlot, BroadcastStatus, Channel
from batch.common.normalize import make_slot_hash, normalize_product_title
from batch.parsers.gmarket_schedule_parser import parse_schedule
from batch.sources.gmarket_schedule import fetch_schedule_html


logger = logging.getLogger("batch.schedule")


def ensure_channel(db: Session, channel_code: str, channel_name: str) -> Channel:
    """채널이 없으면 생성.

    - why: 크롤링 소스가 늘어나면 자동으로 채널이 준비되어야 함.
    """

    channel = db.execute(select(Channel).where(Channel.channel_code == channel_code)).scalar_one_or_none()
    if channel:
        return channel

    channel = Channel(channel_code=channel_code, channel_name=channel_name)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def resolve_status(start_at: datetime, end_at: datetime) -> BroadcastStatus:
    now = datetime.utcnow()
    if start_at > now:
        return BroadcastStatus.SCHEDULED
    if start_at <= now <= end_at:
        return BroadcastStatus.LIVE
    return BroadcastStatus.ENDED


def upsert_slots(db: Session, channel: Channel, source_code: str, items: list[dict]) -> tuple[int, int]:
    """슬롯 업서트 처리.

    - return: (created_count, updated_count)
    """

    created = 0
    updated = 0

    for item in items:
        normalized_title = normalize_product_title(item["raw_title"])
        slot_hash = make_slot_hash(channel.id, item["start_at"], normalized_title)

        existing = db.execute(
            select(BroadcastSlot).where(BroadcastSlot.slot_hash == slot_hash)
        ).scalar_one_or_none()

        if existing:
            existing.end_at = item["end_at"]
            existing.raw_title = item["raw_title"]
            existing.normalized_title = normalized_title
            existing.product_url = item.get("product_url")
            existing.price_text = item.get("price_text")
            existing.image_url = item.get("image_url")
            existing.status = resolve_status(item["start_at"], item["end_at"])
            updated += 1
        else:
            new_slot = BroadcastSlot(
                channel_id=channel.id,
                source_code=source_code,
                start_at=item["start_at"],
                end_at=item["end_at"],
                raw_title=item["raw_title"],
                normalized_title=normalized_title,
                product_url=item.get("product_url"),
                price_text=item.get("price_text"),
                image_url=item.get("image_url"),
                status=resolve_status(item["start_at"], item["end_at"]),
                slot_hash=slot_hash,
            )
            db.add(new_slot)
            created += 1

    db.commit()
    return created, updated


def run_schedule_pipeline(db: Session):
    """편성표 수집 파이프라인 전체 실행."""

    source_code = "gmarket_schedule"
    channel_code = "gmarket"

    html = fetch_schedule_html()
    items = parse_schedule(html)

    if not items:
        logger.warning("파싱 결과가 비어 있습니다. HTML 구조를 확인하세요.")

    channel = ensure_channel(db, channel_code=channel_code, channel_name="G마켓")

    created, updated = upsert_slots(db, channel, source_code, items)
    logger.info("편성표 수집 완료. created=%s updated=%s total=%s", created, updated, len(items))
```

apps/batch/requirements.txt
```
httpx==0.27.2
beautifulsoup4==4.12.3
pandas==2.2.3
SQLAlchemy==2.0.36
pymysql==1.1.1
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
pytest==8.3.3
```

apps/batch/sources/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/sources/gmarket_schedule.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import random
import time
from typing import Optional
import httpx

from batch.common.config import get_batch_settings


def fetch_schedule_html(url: Optional[str] = None) -> str:
    """편성표 HTML을 가져온다.

    - why: 실제 크롤링 대상이 1개라면 fetcher 로직을 단순하게 유지하는 것이 유지보수에 유리.
    """

    settings = get_batch_settings()
    target_url = url or settings.schedule_source_url

    headers = {"User-Agent": settings.user_agent}

    # 요청 간 랜덤 딜레이 (서비스 부하 완화 목적)
    time.sleep(random.uniform(0.3, 1.0))

    retry = 0
    backoff = 1.0

    while True:
        try:
            with httpx.Client(timeout=10.0, headers=headers) as client:
                response = client.get(target_url)
                if response.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError(
                        f"temporary error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError:
            retry += 1
            if retry > 3:
                raise
            time.sleep(backoff)
            backoff *= 2
        except httpx.HTTPError:
            retry += 1
            if retry > 3:
                raise
            time.sleep(backoff)
            backoff *= 2
```

apps/batch/tests/__init__.py
```python
# why: 패키지를 명시적으로 구분하기 위한 빈 init 파일
```

apps/batch/tests/test_normalize.py
```python
# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime

from batch.common.normalize import make_slot_hash, normalize_product_title, parse_price_text


def test_normalize_product_title_removes_noise():
    raw = "[무료배송] 프리미엄 침구 세트!!"
    assert normalize_product_title(raw) == "프리미엄 침구 세트"


def test_parse_price_text_extracts_int():
    assert parse_price_text("12,900원") == 12900


def test_make_slot_hash_changes_by_channel():
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "침구 세트")
    hash2 = make_slot_hash(2, start_at, "침구 세트")
    assert hash1 != hash2
```

apps/web/.env.example
```
# Frontend 환경 변수 예시
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

apps/web/next-env.d.ts
```ts
/// <reference types="next" />
/// <reference types="next/image-types/global" />

// why: Next.js가 자동으로 타입을 로드하도록 참조를 유지하기 위한 주석
```

apps/web/next.config.js
```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

module.exports = nextConfig;
```

apps/web/package.json
```json
{
  "name": "broadcastboard-web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@tanstack/react-query": "5.59.16",
    "antd": "5.21.3",
    "chart.js": "4.4.6",
    "dayjs": "1.11.13",
    "next": "14.2.15",
    "react": "18.3.1",
    "react-chartjs-2": "5.2.0",
    "react-dom": "18.3.1"
  },
  "devDependencies": {
    "@types/node": "22.9.0",
    "@types/react": "18.3.12",
    "@types/react-dom": "18.3.1",
    "typescript": "5.6.3"
  }
}
```

apps/web/src/app/alerts/page.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.page {
  display: grid;
  gap: var(--space-12);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  margin: 0;
}

.subtitle {
  margin: var(--space-4) 0 0;
  color: var(--color-subtext);
}
```

apps/web/src/app/alerts/page.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { Button, message } from "antd";
import { useState } from "react";
import AlertRuleFormModal from "../../components/AlertRuleFormModal";
import AlertRuleTable from "../../components/AlertRuleTable";
import EmptyState from "../../components/EmptyState";
import ErrorState from "../../components/ErrorState";
import LoadingState from "../../components/LoadingState";
import {
  useAlerts,
  useCreateAlert,
  useDeleteAlert,
  useUpdateAlert,
} from "../../features/alerts/useAlerts";
import { Alert } from "../../types/alert";
import styles from "./page.module.css";

export default function AlertsPage() {
  const { data, isLoading, isError } = useAlerts();
  const createMutation = useCreateAlert();
  const updateMutation = useUpdateAlert();
  const deleteMutation = useDeleteAlert();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<Alert | null>(null);

  const handleSubmit = async (payload: any) => {
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, payload });
        message.success("알림이 수정되었습니다.");
      } else {
        await createMutation.mutateAsync(payload);
        message.success("알림이 생성되었습니다.");
      }
      setIsModalOpen(false);
      setEditing(null);
    } catch {
      message.error("저장에 실패했습니다.");
    }
  };

  const handleDelete = async (alertId: number) => {
    try {
      await deleteMutation.mutateAsync(alertId);
      message.success("삭제되었습니다.");
    } catch {
      message.error("삭제에 실패했습니다.");
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>알림 규칙 관리</h1>
          <p className={styles.subtitle}>키워드와 채널 조건으로 알림을 설정합니다.</p>
        </div>
        <Button type="primary" onClick={() => setIsModalOpen(true)}>
          새 알림
        </Button>
      </header>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {!isLoading && !isError && data && data.length === 0 && <EmptyState />}
      {!isLoading && !isError && data && data.length > 0 && (
        <AlertRuleTable
          alerts={data}
          onEdit={(alert) => {
            setEditing(alert);
            setIsModalOpen(true);
          }}
          onDelete={handleDelete}
        />
      )}

      <AlertRuleFormModal
        open={isModalOpen}
        initialData={editing}
        onCancel={() => {
          setIsModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
```

apps/web/src/app/broadcasts/[broadcastId]/page.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.page {
  display: grid;
  gap: var(--space-12);
}

.detailBox {
  padding: var(--space-12);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.adjacent {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-10);
}
```

apps/web/src/app/broadcasts/[broadcastId]/page.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { useParams } from "next/navigation";
import dayjs from "dayjs";
import { useBroadcastDetail } from "../../../features/broadcasts/useBroadcastDetail";
import { useBroadcasts } from "../../../features/broadcasts/useBroadcasts";
import BroadcastDetailHeader from "../../../components/BroadcastDetailHeader";
import AdjacentBroadcastList from "../../../components/AdjacentBroadcastList";
import LoadingState from "../../../components/LoadingState";
import ErrorState from "../../../components/ErrorState";
import styles from "./page.module.css";

export default function BroadcastDetailPage() {
  const params = useParams();
  const broadcastId = params?.broadcastId as string;

  const { data: broadcast, isLoading, isError } = useBroadcastDetail(broadcastId);

  const dateParam = broadcast ? dayjs(broadcast.start_at).format("YYYY-MM-DD") : undefined;
  const { data: dayList } = useBroadcasts({ date: dateParam });

  if (isLoading) return <LoadingState />;
  if (isError || !broadcast) return <ErrorState />;

  const index = dayList?.findIndex((item) => item.id === broadcast.id) ?? -1;
  const prev = index > 0 && dayList ? [dayList[index - 1]] : [];
  const next = dayList && index >= 0 && index < dayList.length - 1 ? [dayList[index + 1]] : [];

  return (
    <div className={styles.page}>
      <BroadcastDetailHeader broadcast={broadcast} />
      <section className={styles.detailBox}>
        <div>
          <h3>상세 정보</h3>
          <p>원본 제목: {broadcast.raw_title}</p>
          <p>정규화 제목: {broadcast.normalized_title}</p>
          <p>가격: {broadcast.price_text || "정보없음"}</p>
          <p>상품 URL: {broadcast.product_url || "정보없음"}</p>
        </div>
      </section>
      <div className={styles.adjacent}>
        <AdjacentBroadcastList title="이전 방송" broadcasts={prev} />
        <AdjacentBroadcastList title="다음 방송" broadcasts={next} />
      </div>
    </div>
  );
}
```

apps/web/src/app/layout.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import type { ReactNode } from "react";
import "antd/dist/reset.css";
import "../styles/globals.css";
import Providers from "../lib/providers";

export const metadata = {
  title: "BroadcastBoard",
  description: "홈쇼핑 편성표 대시보드",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <Providers>
          <main>{children}</main>
        </Providers>
      </body>
    </html>
  );
}
```

apps/web/src/app/page.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.page {
  display: grid;
  gap: var(--space-12);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.title {
  margin: 0;
  font-size: 28px;
}

.subtitle {
  margin: var(--space-4) 0 0;
  color: var(--color-subtext);
}

.filters {
  display: grid;
  grid-template-columns: 160px 200px 1fr;
  gap: var(--space-8);
}

.select {
  width: 100%;
}

.search {
  width: 100%;
}

.content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-12);
  align-items: start;
}
```

apps/web/src/app/page.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { DatePicker, Input, Select } from "antd";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import BroadcastTimeline from "../components/BroadcastTimeline";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import UpcomingBroadcastList from "../components/UpcomingBroadcastList";
import { useBroadcasts } from "../features/broadcasts/useBroadcasts";
import { useChannels } from "../features/broadcasts/useChannels";
import styles from "./page.module.css";

export default function HomePage() {
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [channelCode, setChannelCode] = useState<string | undefined>();
  const [keyword, setKeyword] = useState<string | undefined>();

  const { data: channels } = useChannels();

  const queryParams = useMemo(
    () => ({
      date: selectedDate.format("YYYY-MM-DD"),
      channelCode,
      keyword,
    }),
    [selectedDate, channelCode, keyword]
  );

  const { data, isLoading, isError } = useBroadcasts(queryParams);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>오늘/내일 편성표 타임라인</h1>
          <p className={styles.subtitle}>UTC 기준 데이터를 KST로 표시합니다.</p>
        </div>
      </header>

      <section className={styles.filters}>
        <DatePicker value={selectedDate} onChange={(value) => value && setSelectedDate(value)} />
        <Select
          placeholder="채널 선택"
          allowClear
          options={channels?.map((channel) => ({
            value: channel.channel_code,
            label: channel.channel_name,
          }))}
          onChange={(value) => setChannelCode(value)}
          className={styles.select}
        />
        <Input.Search
          placeholder="키워드 검색"
          onSearch={(value) => setKeyword(value || undefined)}
          className={styles.search}
        />
      </section>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {!isLoading && !isError && data && data.length === 0 && <EmptyState />}

      {!isLoading && !isError && data && data.length > 0 && (
        <div className={styles.content}>
          <BroadcastTimeline broadcasts={data} />
          <UpcomingBroadcastList broadcasts={data} />
        </div>
      )}
    </div>
  );
}
```

apps/web/src/app/trends/page.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.page {
  display: grid;
  gap: var(--space-12);
}

.header {
  display: grid;
  gap: var(--space-4);
}

.title {
  margin: 0;
}

.subtitle {
  margin: 0;
  color: var(--color-subtext);
}

.chartBox {
  background: var(--color-surface);
  padding: var(--space-12);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}
```

apps/web/src/app/trends/page.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import dayjs from "dayjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import LoadingState from "../../components/LoadingState";
import ErrorState from "../../components/ErrorState";
import { useBroadcasts } from "../../features/broadcasts/useBroadcasts";
import styles from "./page.module.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function buildHourlyCounts(times: string[]) {
  const counts = new Array(24).fill(0);
  times.forEach((time) => {
    const hour = dayjs(time).hour();
    counts[hour] += 1;
  });
  return counts;
}

export default function TrendsPage() {
  const today = dayjs().format("YYYY-MM-DD");
  const { data, isLoading, isError } = useBroadcasts({ date: today });

  if (isLoading) return <LoadingState />;
  if (isError || !data) return <ErrorState />;

  const labels = Array.from({ length: 24 }, (_, idx) => `${idx}:00`);
  const counts = buildHourlyCounts(data.map((item) => item.start_at));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>방송 트렌드</h1>
        <p className={styles.subtitle}>시간대별 방송 개수 (UTC 기준)</p>
      </header>
      <div className={styles.chartBox}>
        <Bar
          data={{
            labels,
            datasets: [
              {
                label: "편성 슬롯",
                data: counts,
                backgroundColor: "rgba(56, 189, 248, 0.6)",
              },
            ],
          }}
          options={{
            responsive: true,
            plugins: {
              legend: { position: "top" as const },
              title: { display: false },
            },
          }}
        />
      </div>
    </div>
  );
}
```

apps/web/src/components/AdjacentBroadcastList.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.box {
  background: var(--color-surface);
  padding: var(--space-10);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.title {
  margin: 0 0 var(--space-6);
}

.list {
  display: grid;
  gap: var(--space-4);
}

.item {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: var(--space-6);
  font-size: 14px;
  color: var(--color-subtext);
}

.text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

apps/web/src/components/AdjacentBroadcastList.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import dayjs from "dayjs";
import { Broadcast } from "../types/broadcast";
import styles from "./AdjacentBroadcastList.module.css";

export default function AdjacentBroadcastList({
  title,
  broadcasts,
}: {
  title: string;
  broadcasts: Broadcast[];
}) {
  return (
    <div className={styles.box}>
      <h4 className={styles.title}>{title}</h4>
      <div className={styles.list}>
        {broadcasts.map((item) => (
          <div key={item.id} className={styles.item}>
            <span>{dayjs(item.start_at).format("HH:mm")}</span>
            <span className={styles.text}>{item.raw_title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

apps/web/src/components/AlertRuleFormModal.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Modal, Form, Input, InputNumber, Select, Switch } from "antd";
import { useEffect } from "react";
import { Alert, AlertCreatePayload, AlertUpdatePayload } from "../types/alert";

const destinationOptions = [
  { value: "SLACK", label: "Slack" },
  { value: "EMAIL", label: "Email" },
];

function joinList(value?: string[] | null) {
  return value ? value.join(", ") : "";
}

function splitList(value?: string) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function AlertRuleFormModal({
  open,
  initialData,
  onCancel,
  onSubmit,
}: {
  open: boolean;
  initialData?: Alert | null;
  onCancel: () => void;
  onSubmit: (payload: AlertCreatePayload | AlertUpdatePayload) => void;
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (initialData) {
      form.setFieldsValue({
        alert_name: initialData.alert_name,
        target_channel_codes: joinList(initialData.target_channel_codes),
        keyword_list: joinList(initialData.keyword_list),
        category_list: joinList(initialData.category_list),
        notify_before_minutes: initialData.notify_before_minutes,
        destination_type: initialData.destination_type,
        destination_value: initialData.destination_value,
        is_active: initialData.is_active,
      });
    } else {
      form.resetFields();
    }
  }, [initialData, form]);

  return (
    <Modal
      title={initialData ? "알림 수정" : "알림 생성"}
      open={open}
      onCancel={onCancel}
      onOk={() => {
        form.validateFields().then((values) => {
          const payload = {
            ...values,
            target_channel_codes: splitList(values.target_channel_codes),
            keyword_list: splitList(values.keyword_list),
            category_list: splitList(values.category_list),
          };
          onSubmit(payload);
        });
      }}
    >
      <Form form={form} layout="vertical" initialValues={{ notify_before_minutes: 30, is_active: true }}>
        <Form.Item label="알림명" name="alert_name" rules={[{ required: true }]}>
          <Input placeholder="예: 야간 침구 알림" />
        </Form.Item>
        <Form.Item label="채널 코드" name="target_channel_codes" rules={[{ required: true }]}>
          <Input placeholder="cjon, hmall" />
        </Form.Item>
        <Form.Item label="키워드" name="keyword_list" rules={[{ required: true }]}>
          <Input placeholder="침구, 매트리스" />
        </Form.Item>
        <Form.Item label="카테고리" name="category_list">
          <Input placeholder="(선택) 리빙, 패션" />
        </Form.Item>
        <Form.Item label="알림 전(분)" name="notify_before_minutes">
          <InputNumber min={0} max={1440} style={{ width: "100%" }} />
        </Form.Item>
        <Form.Item label="목적지" name="destination_type">
          <Select options={destinationOptions} />
        </Form.Item>
        <Form.Item label="웹훅/주소" name="destination_value" rules={[{ required: true }]}>
          <Input placeholder="Slack Webhook URL" />
        </Form.Item>
        <Form.Item label="활성" name="is_active" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  );
}
```

apps/web/src/components/AlertRuleTable.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Table, Button, Space, Tag } from "antd";
import type { ColumnsType } from "antd/es/table";
import { Alert } from "../types/alert";

export default function AlertRuleTable({
  alerts,
  onEdit,
  onDelete,
}: {
  alerts: Alert[];
  onEdit: (alert: Alert) => void;
  onDelete: (alertId: number) => void;
}) {
  const columns: ColumnsType<Alert> = [
    {
      title: "알림명",
      dataIndex: "alert_name",
    },
    {
      title: "채널",
      dataIndex: "target_channel_codes",
      render: (codes: string[]) => (
        <Space wrap>
          {codes.map((code) => (
            <Tag key={code}>{code}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: "키워드",
      dataIndex: "keyword_list",
      render: (keywords: string[]) => keywords.join(", "),
    },
    {
      title: "알림 전(분)",
      dataIndex: "notify_before_minutes",
    },
    {
      title: "상태",
      dataIndex: "is_active",
      render: (active: boolean) => (active ? "활성" : "비활성"),
    },
    {
      title: "액션",
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => onEdit(record)}>
            수정
          </Button>
          <Button danger size="small" onClick={() => onDelete(record.id)}>
            삭제
          </Button>
        </Space>
      ),
    },
  ];

  return <Table rowKey="id" columns={columns} dataSource={alerts} pagination={false} />;
}
```

apps/web/src/components/BroadcastCard.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-10);
  display: grid;
  gap: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: var(--color-subtext);
}

.time {
  font-weight: 600;
}

.status {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(56, 189, 248, 0.2);
}

.title {
  margin: 0;
  font-size: 18px;
  line-height: 1.4;
  color: var(--color-text);
}

.meta {
  margin: 0;
  color: var(--color-subtext);
  font-size: 14px;
}
```

apps/web/src/components/BroadcastCard.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import Link from "next/link";
import dayjs from "dayjs";
import { Broadcast } from "../types/broadcast";
import styles from "./BroadcastCard.module.css";

export default function BroadcastCard({ broadcast }: { broadcast: Broadcast }) {
  return (
    <Link href={`/broadcasts/${broadcast.id}`} className={styles.card}>
      <div className={styles.header}>
        <span className={styles.time}>
          {dayjs(broadcast.start_at).format("HH:mm")}
        </span>
        <span className={styles.status}>{broadcast.status}</span>
      </div>
      <h3 className={styles.title}>{broadcast.raw_title}</h3>
      <p className={styles.meta}>가격: {broadcast.price_text || "정보없음"}</p>
    </Link>
  );
}
```

apps/web/src/components/BroadcastDetailHeader.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-12);
  background: var(--color-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  gap: var(--space-10);
}

.title {
  margin: 0 0 var(--space-4);
}

.meta {
  margin: 0;
  color: var(--color-subtext);
}

.badge {
  background: rgba(56, 189, 248, 0.2);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
}
```

apps/web/src/components/BroadcastDetailHeader.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import dayjs from "dayjs";
import { Broadcast } from "../types/broadcast";
import styles from "./BroadcastDetailHeader.module.css";

export default function BroadcastDetailHeader({ broadcast }: { broadcast: Broadcast }) {
  return (
    <div className={styles.header}>
      <div>
        <h2 className={styles.title}>{broadcast.raw_title}</h2>
        <p className={styles.meta}>
          {dayjs(broadcast.start_at).format("YYYY-MM-DD HH:mm")} ~ {dayjs(broadcast.end_at).format("HH:mm")}
        </p>
      </div>
      <div className={styles.badge}>{broadcast.status}</div>
    </div>
  );
}
```

apps/web/src/components/BroadcastTimeline.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.timeline {
  display: grid;
  gap: var(--space-12);
}

.group {
  display: grid;
  gap: var(--space-8);
}

.hourLabel {
  font-weight: 600;
  color: var(--color-accent);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-10);
}
```

apps/web/src/components/BroadcastTimeline.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import dayjs from "dayjs";
import { Broadcast } from "../types/broadcast";
import BroadcastCard from "./BroadcastCard";
import styles from "./BroadcastTimeline.module.css";

function groupByHour(broadcasts: Broadcast[]) {
  const groups: Record<string, Broadcast[]> = {};
  broadcasts.forEach((item) => {
    const key = dayjs(item.start_at).format("HH:00");
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  });
  return groups;
}

export default function BroadcastTimeline({ broadcasts }: { broadcasts: Broadcast[] }) {
  const groups = groupByHour(broadcasts);
  const hours = Object.keys(groups).sort();

  return (
    <div className={styles.timeline}>
      {hours.map((hour) => (
        <section key={hour} className={styles.group}>
          <div className={styles.hourLabel}>{hour}</div>
          <div className={styles.cards}>
            {groups[hour].map((item) => (
              <BroadcastCard key={item.id} broadcast={item} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
```

apps/web/src/components/EmptyState.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import styles from "./State.module.css";

export default function EmptyState({
  title = "데이터가 없습니다",
  description = "조건을 변경해 다시 확인해 주세요.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className={styles.stateBox}>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
```

apps/web/src/components/ErrorState.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import styles from "./State.module.css";

export default function ErrorState({
  title = "오류가 발생했습니다",
  description = "잠시 후 다시 시도해 주세요.",
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className={styles.stateBox}>
      <strong className={styles.error}>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
```

apps/web/src/components/LoadingState.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { Spin } from "antd";
import styles from "./State.module.css";

export default function LoadingState({ label = "로딩 중입니다" }: { label?: string }) {
  return (
    <div className={styles.stateBox}>
      <Spin size="large" />
      <p>{label}</p>
    </div>
  );
}
```

apps/web/src/components/State.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.stateBox {
  padding: var(--space-16);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  text-align: center;
  color: var(--color-subtext);
  display: grid;
  gap: var(--space-6);
  place-items: center;
}

.error {
  color: var(--color-danger);
}
```

apps/web/src/components/UpcomingBroadcastList.module.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
.box {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-10);
}

.title {
  margin: 0 0 var(--space-6);
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-4);
}

.item {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: var(--space-6);
  font-size: 14px;
  color: var(--color-subtext);
}

.text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

apps/web/src/components/UpcomingBroadcastList.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import dayjs from "dayjs";
import { Broadcast } from "../types/broadcast";
import styles from "./UpcomingBroadcastList.module.css";

export default function UpcomingBroadcastList({ broadcasts }: { broadcasts: Broadcast[] }) {
  const upcoming = broadcasts.slice(0, 5);

  return (
    <div className={styles.box}>
      <h4 className={styles.title}>곧 시작하는 방송</h4>
      <ul className={styles.list}>
        {upcoming.map((item) => (
          <li key={item.id} className={styles.item}>
            <span>{dayjs(item.start_at).format("HH:mm")}</span>
            <span className={styles.text}>{item.raw_title}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

apps/web/src/features/alerts/useAlerts.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiPatch, apiPost, apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Alert, AlertCreatePayload, AlertUpdatePayload } from "../../types/alert";

export function useAlerts() {
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: () => apiGet<Alert[]>("/api/v1/alerts"),
  });
}

export function useCreateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AlertCreatePayload) => apiPost<Alert, AlertCreatePayload>("/api/v1/alerts", payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}

export function useUpdateAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: AlertUpdatePayload }) =>
      apiPatch<Alert, AlertUpdatePayload>(`/api/v1/alerts/${id}`, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}

export function useDeleteAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiDelete<{ deleted: boolean }>(`/api/v1/alerts/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts }),
  });
}
```

apps/web/src/features/broadcasts/useBroadcastDetail.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Broadcast } from "../../types/broadcast";

export function useBroadcastDetail(broadcastId: string | number) {
  return useQuery({
    queryKey: queryKeys.broadcastDetail(broadcastId),
    queryFn: () => apiGet<Broadcast>(`/api/v1/broadcasts/${broadcastId}`),
  });
}
```

apps/web/src/features/broadcasts/useBroadcasts.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Broadcast } from "../../types/broadcast";

export interface BroadcastQueryParams {
  date?: string;
  channelCode?: string;
  keyword?: string;
  status?: string;
}

export function useBroadcasts(params: BroadcastQueryParams) {
  return useQuery({
    queryKey: queryKeys.broadcasts(params),
    queryFn: () => {
      const query = new URLSearchParams();
      if (params.date) query.append("date", params.date);
      if (params.channelCode) query.append("channelCode", params.channelCode);
      if (params.keyword) query.append("keyword", params.keyword);
      if (params.status) query.append("status", params.status);

      const queryString = query.toString();
      return apiGet<Broadcast[]>(`/api/v1/broadcasts${queryString ? `?${queryString}` : ""}`);
    },
  });
}
```

apps/web/src/features/broadcasts/useChannels.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../../lib/apiClient";
import { queryKeys } from "../../lib/queryKeys";
import { Channel } from "../../types/channel";

export function useChannels() {
  return useQuery({
    queryKey: queryKeys.channels,
    queryFn: () => apiGet<Channel[]>("/api/v1/channels"),
  });
}
```

apps/web/src/lib/apiClient.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
import { ApiResponse } from "../types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  meta?: Record<string, unknown>;

  constructor(message: string, status: number, meta?: Record<string, unknown>) {
    super(message);
    this.status = status;
    this.meta = meta;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as ApiResponse<T>;
  if (!response.ok) {
    throw new ApiError(payload.meta?.message || "요청 실패", response.status, payload.meta);
  }
  return payload.data;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });
  return handleResponse<T>(response);
}

export async function apiPost<T, P>(path: string, body: P): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

export async function apiPatch<T, P>(path: string, body: P): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

export async function apiDelete<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });
  return handleResponse<T>(response);
}

export { ApiError };
```

apps/web/src/lib/providers.tsx
```tsx
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
"use client";

import { PropsWithChildren } from "react";
import { ConfigProvider, theme } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,
      retry: 1,
    },
  },
});

export default function Providers({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          algorithm: theme.darkAlgorithm,
          token: {
            colorPrimary: "#38bdf8",
            borderRadius: 10,
          },
        }}
      >
        {children}
      </ConfigProvider>
    </QueryClientProvider>
  );
}
```

apps/web/src/lib/queryKeys.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export const queryKeys = {
  channels: ["channels"] as const,
  broadcasts: (params: Record<string, string | undefined>) =>
    ["broadcasts", params] as const,
  broadcastDetail: (id: string | number) => ["broadcast", id] as const,
  alerts: ["alerts"] as const,
};
```

apps/web/src/styles/globals.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
@import url("./tokens.css");

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: var(--font-base);
  background: var(--color-bg);
  color: var(--color-text);
}

a {
  color: inherit;
  text-decoration: none;
}

main {
  min-height: 100vh;
  padding: var(--space-16);
}
```

apps/web/src/styles/tokens.css
```css
/* why: UI 일관성과 가독성을 위해 스타일 의도를 명시 */
:root {
  --color-bg: #0f172a;
  --color-surface: #111827;
  --color-card: #1f2937;
  --color-text: #f9fafb;
  --color-subtext: #cbd5f5;
  --color-accent: #38bdf8;
  --color-danger: #f87171;
  --color-border: rgba(148, 163, 184, 0.2);

  --font-base: "Inter", "Pretendard", system-ui, sans-serif;
  --font-size-base: 16px;

  --space-2: 4px;
  --space-4: 8px;
  --space-6: 12px;
  --space-8: 16px;
  --space-10: 20px;
  --space-12: 24px;
  --space-16: 32px;
  --space-20: 40px;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;

  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 8px 20px rgba(0, 0, 0, 0.3);
}
```

apps/web/src/types/alert.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export type DestinationType = "SLACK" | "EMAIL";

export interface Alert {
  id: number;
  alert_name: string;
  target_channel_codes: string[];
  keyword_list: string[];
  category_list?: string[] | null;
  notify_before_minutes: number;
  destination_type: DestinationType;
  destination_value: string;
  is_active: boolean;
}

export interface AlertCreatePayload {
  alert_name: string;
  target_channel_codes: string[];
  keyword_list: string[];
  category_list?: string[] | null;
  notify_before_minutes: number;
  destination_type: DestinationType;
  destination_value: string;
  is_active: boolean;
}

export type AlertUpdatePayload = Partial<AlertCreatePayload>;
```

apps/web/src/types/api.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export interface ResponseMeta {
  count?: number;
  message?: string;
  time_policy?: string;
}

export interface ApiResponse<T> {
  data: T;
  meta: ResponseMeta;
}
```

apps/web/src/types/broadcast.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export type BroadcastStatus = "SCHEDULED" | "LIVE" | "ENDED";

export interface Broadcast {
  id: number;
  channel_id: number;
  source_code: string;
  start_at: string;
  end_at: string;
  raw_title: string;
  normalized_title: string;
  product_url?: string | null;
  price_text?: string | null;
  image_url?: string | null;
  status: BroadcastStatus;
  slot_hash: string;
}
```

apps/web/src/types/channel.ts
```ts
// why: 파일 책임을 명확히 하고 유지보수를 쉽게 하기 위한 설명 주석
export interface Channel {
  id: number;
  channel_code: string;
  channel_name: string;
  channel_logo_url?: string | null;
}
```

apps/web/tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true
  },
  "include": ["next-env.d.ts", "src/**/*.ts", "src/**/*.tsx"],
  "exclude": ["node_modules"]
}
```
