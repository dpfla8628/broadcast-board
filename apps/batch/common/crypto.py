# why: 알림 목적지 값을 DB에서 읽을 때 복호화하기 위한 유틸
from cryptography.fernet import Fernet, InvalidToken

from common.config import get_batch_settings


def _get_fernet() -> Fernet:
    settings = get_batch_settings()
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY가 설정되지 않았습니다.")
    return Fernet(settings.encryption_key.encode("utf-8"))


def decrypt_value(value: str) -> str:
    if value is None:
        return value
    fernet = _get_fernet()
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")


def is_invalid_token(exc: Exception) -> bool:
    return isinstance(exc, InvalidToken)
