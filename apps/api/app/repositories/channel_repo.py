# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.models.channel import Channel


class ChannelRepository:
    """채널 데이터 접근 계층.

    - why: 서비스 계층에서 SQLAlchemy 세부 구현을 숨기기 위해.
    """

    def list_channels(self, db: Session) -> list[Channel]:
        return db.query(Channel).order_by(Channel.channel_name.asc()).all()
