# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import logging

from common.db import get_db_session
from pipelines.schedule_pipeline import run_schedule_pipeline


logger = logging.getLogger("batch.fetch")


def fetch_schedule_job():
    """편성표 수집 잡."""

    db = get_db_session()
    try:
        run_schedule_pipeline(db)
    finally:
        db.close()
