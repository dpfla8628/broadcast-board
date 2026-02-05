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
