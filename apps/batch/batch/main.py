# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import argparse
import logging

from jobs.fetch_schedule_job import fetch_schedule_job
from jobs.send_alerts_job import send_alerts_job


def setup_logging():
    # why: 배치 로그는 실패 원인과 수집 통계를 남겨야 하므로 간단한 표준 포맷 사용
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="BroadcastBoard Batch Runner")
    parser.add_argument(
        "job",
        choices=["fetch_schedule", "send_alerts", "sync_live_streams"],
        help="실행할 배치 작업 이름",
    )
    args = parser.parse_args()

    if args.job == "fetch_schedule":
        fetch_schedule_job()
    elif args.job == "send_alerts":
        send_alerts_job()
    elif args.job == "sync_live_streams":
        # why: playwright 의존성을 사용하는 작업이므로 필요할 때만 import
        from jobs.sync_live_streams_job import sync_live_streams_job

        sync_live_streams_job()


if __name__ == "__main__":
    main()
