# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.models.broadcast_slot import BroadcastSlot, BroadcastStatus
from app.models.broadcast_price_history import BroadcastPriceHistory


class BroadcastRepository:
    """방송 슬롯 데이터 접근 계층."""

    def list_broadcasts(
        self,
        db: Session,
        target_date: date | None = None,
        channel_code: str | None = None,
        keyword: str | None = None,
        categories: list[str] | None = None,
        status: BroadcastStatus | None = None,
    ) -> list[BroadcastSlot]:
        query = db.query(BroadcastSlot).options(selectinload(BroadcastSlot.channel))

        if channel_code:
            # 채널 코드는 Channel 테이블을 조인해 필터링
            from app.models.channel import Channel

            query = query.join(Channel).filter(Channel.channel_code == channel_code)

        if keyword:
            query = query.filter(BroadcastSlot.normalized_title.ilike(f"%{keyword}%"))

        if categories:
            query = query.filter(BroadcastSlot.category.in_(categories))

        if status:
            query = query.filter(BroadcastSlot.status == status)

        if target_date:
            # KST(UTC+9) 기준 날짜를 UTC 범위로 변환해 필터링
            # why: DB는 UTC로 저장하지만, 사용자는 KST 날짜를 기준으로 조회하므로 9시간 보정을 적용
            kst = ZoneInfo("Asia/Seoul")
            start_kst = datetime.combine(target_date, datetime.min.time(), tzinfo=kst)
            end_kst = start_kst + timedelta(days=1)
            start_dt = start_kst.astimezone(timezone.utc).replace(tzinfo=None)
            end_dt = end_kst.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.filter(
                and_(BroadcastSlot.start_at >= start_dt, BroadcastSlot.start_at < end_dt)
            )

        return query.order_by(BroadcastSlot.start_at.asc()).all()

    def get_broadcast(self, db: Session, broadcast_id: int) -> BroadcastSlot | None:
        return (
            db.query(BroadcastSlot)
            .options(selectinload(BroadcastSlot.channel))
            .filter(BroadcastSlot.id == broadcast_id)
            .first()
        )

    def list_price_history(
        self, db: Session, broadcast_id: int
    ) -> list[BroadcastPriceHistory]:
        return (
            db.query(BroadcastPriceHistory)
            .filter(BroadcastPriceHistory.broadcast_slot_id == broadcast_id)
            .order_by(BroadcastPriceHistory.collected_at.asc())
            .all()
        )
