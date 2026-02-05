# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import httpx


def send_slack_message(webhook_url: str, text: str) -> None:
    """슬랙 웹훅으로 메시지 발송.

    - why: MVP의 알림 채널을 단순화하기 위해 webhook 방식 사용.
    """

    if not webhook_url:
        raise ValueError("Slack webhook URL이 비어 있습니다.")

    with httpx.Client(timeout=10.0) as client:
        response = client.post(webhook_url, json={"text": text})
        response.raise_for_status()
