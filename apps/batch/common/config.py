# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BatchSettings(BaseSettings):
    """배치 실행 설정.

    - why: 크롤링 URL, 슬랙 웹훅 등 환경 별로 달라지는 값을 안전하게 관리.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(
        default="mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local"
    )
    schedule_source_url: str = Field(
        default="https://mobile.gmarket.co.kr/HomeShopping/BroadcastSchedule",
        description="G마켓 모바일 홈쇼핑 편성표 URL",
    )
    product_price_fetch_enabled: bool = True
    product_price_fetch_max: int = 200
    product_price_fetch_browser_fallback: bool = True
    product_price_fetch_browser_max: int = 30
    product_price_fetch_concurrency: int = 8
    product_price_fetch_browser_concurrency: int = 3
    product_price_fetch_browser_timeout_sec: int = 60
    product_price_playwright_storage_state_path: str | None = None
    product_price_playwright_headful: bool = False
    live_stream_schedule_url: str = Field(
        default="https://m.livehs.co.kr/schedule",
        description="라이브 스트림 목록 페이지 URL",
    )
    slack_webhook_url: str | None = None
    user_agent: str = "BroadcastBoardBatch/1.0 (+https://local)"

    # 이메일 발송용 SMTP 설정 (옵션)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "BroadcastBoard"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # 알림 목적지 암복호화 키 (Fernet)
    encryption_key: str | None = None


@lru_cache
def get_batch_settings() -> BatchSettings:
    return BatchSettings()
