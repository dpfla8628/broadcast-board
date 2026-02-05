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
        category: str | None,
        status: BroadcastStatus | None,
    ):
        categories = None
        if category:
            categories = [item for item in category.split(",") if item]
        return self.repo.list_broadcasts(
            db, target_date, channel_code, keyword, categories, status
        )

    def get_broadcast(self, db: Session, broadcast_id: int):
        broadcast = self.repo.get_broadcast(db, broadcast_id)
        if not broadcast:
            raise AppError(status_code=404, message="방송 정보를 찾을 수 없습니다.", code="NOT_FOUND")
        return broadcast

    def list_price_history(self, db: Session, broadcast_id: int):
        broadcast = self.repo.get_broadcast(db, broadcast_id)
        if not broadcast:
            raise AppError(status_code=404, message="방송 정보를 찾을 수 없습니다.", code="NOT_FOUND")
        return self.repo.list_price_history(db, broadcast_id)
