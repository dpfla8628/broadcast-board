# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import hashlib
from datetime import datetime


def make_slot_hash(channel_id: int, start_at: datetime, normalized_title: str) -> str:
    """방송 슬롯 고유 해시 생성.

    - 왜 해시를 쓰나: (채널+시작시간+정규화 제목) 조합이 사실상 유일하지만,
      인덱스 길이와 저장 비용을 줄이기 위해 고정 길이 해시를 사용.
    """

    base = f"{channel_id}|{start_at.isoformat()}|{normalized_title}".lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
