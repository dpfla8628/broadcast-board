# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime

from common.normalize import infer_category, make_slot_hash, normalize_product_title, parse_price_text


def test_normalize_product_title_removes_noise():
    raw = "[무료배송] 프리미엄 침구 세트!!"
    assert normalize_product_title(raw) == "프리미엄 침구 세트"


def test_parse_price_text_extracts_int():
    assert parse_price_text("12,900원") == 12900


def test_make_slot_hash_changes_by_channel():
    start_at = datetime(2026, 2, 3, 9, 0, 0)
    hash1 = make_slot_hash(1, start_at, "침구 세트")
    hash2 = make_slot_hash(2, start_at, "침구 세트")
    assert hash1 != hash2


def test_infer_category_rule_based():
    assert infer_category("프리미엄 침구 세트") == "리빙"
