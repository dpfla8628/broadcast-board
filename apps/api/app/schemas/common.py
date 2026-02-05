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
