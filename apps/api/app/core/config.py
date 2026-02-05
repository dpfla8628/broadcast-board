# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from functools import lru_cache
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정을 환경변수에서 읽어오는 클래스.

    - 왜 BaseSettings를 쓰나: 실행 환경마다 다른 값을 안전하게 주입하기 위해서.
    - env 파일을 직접 로드하는 대신, pydantic-settings 표준을 활용해 일관성을 유지.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "BroadcastBoard API"
    app_env: str = Field(default="local", description="dev|staging|prod")
    database_url: str = Field(
        default="mysql+pymysql://nkshop_user:nkshop_password_1234@localhost:3306/nkshop_local",
        description="SQLAlchemy 접속 문자열",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="허용할 프론트엔드 오리진",
    )
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # API 응답의 시간대 정책을 명시적으로 노출하기 위해 사용
    time_policy: str = "UTC"

    # 알림 목적지 값을 암복호화하기 위한 키 (Fernet, base64)
    encryption_key: str = Field(default="", description="Fernet key for encrypting secrets")


@lru_cache
def get_settings() -> Settings:
    return Settings()
