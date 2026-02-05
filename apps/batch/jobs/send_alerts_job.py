# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime, timedelta
import logging

from sqlalchemy import select

from common.config import get_batch_settings
from common.db import get_db_session
from common.crypto import decrypt_value, is_invalid_token
from common.models import Alert, BroadcastSlot, Channel, DestinationType
from common.email import send_email_message
from common.slack import send_slack_message


logger = logging.getLogger("batch.alerts")


def _match_keywords(title: str, keywords: list[str]) -> bool:
    # why: 키워드 매칭을 단순화하여 빠른 MVP 구현을 보장
    lowered = title.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def send_alerts_job():
    """알림 발송 잡.

    - 오늘 편성표 중 키워드 매칭 & 시작 전 N분 조건을 만족하면 Slack/Email로 발송.
    """

    settings = get_batch_settings()
    db = get_db_session()

    now = datetime.utcnow()

    try:
        alerts = db.execute(select(Alert).where(Alert.is_active == True)).scalars().all()
        sent_count = 0

        for alert in alerts:
            if not alert.destination_value:
                continue

            try:
                destination_value = decrypt_value(alert.destination_value)
            except Exception as exc:
                if is_invalid_token(exc):
                    # 기존 평문 데이터일 수 있어 그대로 사용
                    destination_value = alert.destination_value
                else:
                    raise

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
                if alert.destination_type == DestinationType.SLACK:
                    send_slack_message(destination_value, message)
                    sent_count += 1
                elif alert.destination_type == DestinationType.EMAIL:
                    subject = f"[BroadcastBoard] {alert.alert_name}"
                    send_email_message(destination_value, subject, message)
                    sent_count += 1
                else:
                    continue

        logger.info("알림 발송 완료. sent=%s", sent_count)
    finally:
        db.close()
