# why: Playwright로 수집한 스트림 URL을 채널 테이블에 반영하기 위한 배치 작업
import logging

from sqlalchemy import select

from common.db import get_db_session
from common.models import Channel
from sources.live_streams import collect_live_streams


logger = logging.getLogger("batch.sync_live_streams")


def sync_live_streams_job() -> None:
    with get_db_session() as db:
        channels = db.execute(select(Channel)).scalars().all()
        channel_name_map = {
            channel.channel_name: channel.channel_code for channel in channels if channel.channel_name
        }

        result = collect_live_streams(channel_name_map)

        if not result.matched:
            logger.warning("매칭된 스트림 URL이 없습니다. 리포트를 확인하세요.")
            return

        for channel_code, stream_url in result.matched.items():
            channel = next((item for item in channels if item.channel_code == channel_code), None)
            if not channel:
                continue
            channel.channel_stream_url = stream_url
        db.commit()

    logger.info("채널 스트림 URL 업데이트 완료")
