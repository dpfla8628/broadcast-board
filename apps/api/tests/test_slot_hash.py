# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
from app.core.utils import make_slot_hash


def test_make_slot_hash_is_deterministic():
    # 같은 입력이면 항상 같은 해시가 나와야 중복 방지가 가능
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    hash2 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    assert hash1 == hash2


def test_make_slot_hash_changes_by_title():
    # 제목이 달라지면 다른 슬롯으로 간주해야 하므로 해시도 달라져야 함
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "프리미엄 침구 세트")
    hash2 = make_slot_hash(1, start_at, "프리미엄 침구 세트 2")
    assert hash1 != hash2
