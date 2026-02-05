# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.broadcast_slot import BroadcastStatus
from app.schemas.broadcast import BroadcastDetailOut, BroadcastOut, PriceHistoryOut
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
    category: str | None = Query(default=None),
    status: BroadcastStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    broadcasts = service.list_broadcasts(db, date_param, channel_code, keyword, category, status)
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


@router.get("/{broadcast_id}/price-history", response_model=ApiResponse[list[PriceHistoryOut]])
def get_price_history(broadcast_id: int, db: Session = Depends(get_db)):
    history = service.list_price_history(db, broadcast_id)
    return ApiResponse(
        data=history,
        meta=ResponseMeta(count=len(history), time_policy=settings.time_policy),
    )
