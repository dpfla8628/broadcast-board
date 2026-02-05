# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.repositories.channel_repo import ChannelRepository


class ChannelService:
    """채널 서비스 계층."""

    def __init__(self) -> None:
        self.repo = ChannelRepository()

    def list_channels(self, db: Session):
        return self.repo.list_channels(db)
