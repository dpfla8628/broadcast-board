# why: 민감 정보(알림 목적지 등)를 DB에 저장할 때 암복호화하기 위한 유틸
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY가 설정되지 않았습니다.")

    key = settings.encryption_key.encode("utf-8")
    return Fernet(key)


def encrypt_value(value: str) -> str:
    if value is None:
        return value
    fernet = _get_fernet()
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str) -> str:
    if value is None:
        return value
    fernet = _get_fernet()
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")


def is_invalid_token(exc: Exception) -> bool:
    return isinstance(exc, InvalidToken)
