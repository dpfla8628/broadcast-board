# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import hashlib
import re
from datetime import datetime


UNWANTED_KEYWORDS = [
    "무료배송",
    "단독",
    "특가",
    "방송중",
    "오늘만",
    "기획전",
]

# 간단한 룰 기반 카테고리 분류 사전
CATEGORY_RULES: dict[str, list[str]] = {
    "식품": [
        "식품",
        "간식",
        "과자",
        "초콜릿",
        "커피",
        "차",
        "주스",
        "음료",
        "김치",
        "한우",
        "소고기",
        "돼지고기",
        "닭",
        "해산물",
        "생선",
        "과일",
        "채소",
        "견과",
        "두유",
    ],
    "의류": [
        "의류",
        "티셔츠",
        "셔츠",
        "자켓",
        "점퍼",
        "패딩",
        "바지",
        "데님",
        "원피스",
        "니트",
        "가디건",
        "후드",
        "운동복",
    ],
    "리빙": [
        "침구",
        "이불",
        "베개",
        "매트리스",
        "커튼",
        "소파",
        "의자",
        "테이블",
        "주방",
        "수납",
        "청소",
        "세제",
        "수건",
    ],
    "가전": [
        "가전",
        "TV",
        "세탁기",
        "건조기",
        "냉장고",
        "에어컨",
        "청소기",
        "공기청정기",
        "노트북",
        "스마트폰",
        "이어폰",
        "오디오",
    ],
    "뷰티": [
        "화장품",
        "스킨",
        "로션",
        "크림",
        "팩",
        "앰플",
        "헤어",
        "샴푸",
        "린스",
        "향수",
    ],
    "건강": [
        "건강",
        "비타민",
        "영양제",
        "홍삼",
        "프로바이오틱",
        "오메가",
        "단백질",
    ],
    "패션잡화": [
        "가방",
        "지갑",
        "신발",
        "운동화",
        "샌들",
        "모자",
        "시계",
        "주얼리",
    ],
}


def normalize_product_title(raw_title: str) -> str:
    """상품명 정규화.

    - why: 서로 다른 표기(특수문자/이모지/불필요 키워드)가 있어도 같은 상품으로 인식해야
      슬롯 중복을 막고 검색 경험을 개선할 수 있음.
    """

    if not raw_title:
        return ""

    title = raw_title
    for keyword in UNWANTED_KEYWORDS:
        title = title.replace(keyword, "")

    # 특수문자를 공백으로 치환해 단어 단위 비교가 가능하도록 처리
    title = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", title)
    # 연속 공백은 하나로 줄여 비교/검색을 안정화
    title = re.sub(r"\s+", " ", title)

    return title.strip().lower()


def parse_price_text(price_text: str | None) -> int | None:
    """가격 문자열에서 정수만 추출.

    - why: '12,900원' 같은 표기를 숫자로 변환해 차트나 필터에 활용하기 위해.
    """

    if not price_text:
        return None

    match = re.search(r"\d[\d,]*(?:\\.\\d+)?", price_text)
    if not match:
        return None

    value = match.group(0).split(".")[0]
    return int(value.replace(",", ""))


def calculate_discount_rate(original_price: int | None, sale_price: int | None) -> float | None:
    """정가 대비 할인율 계산.

    - why: 여러 소스에서 가격을 합친 뒤에도 동일한 규칙으로 할인율을 계산하기 위해.
    """

    if original_price and sale_price and original_price > 0 and sale_price <= original_price:
        return round((original_price - sale_price) / original_price * 100, 1)
    return None


def parse_price_info(price_text: str | None) -> tuple[int | None, int | None, float | None]:
    """가격 문자열에서 정가/할인가/할인율을 추정.

    - why: 방송 화면에서 정가/할인가가 함께 노출되는 경우가 있어 자동 추정을 지원
    """

    if not price_text:
        return None, None, None

    numbers = re.findall(r"\d[\d,]*", price_text)
    if not numbers:
        return None, None, None

    values = [int(num.replace(",", "")) for num in numbers]

    # 정가/할인가가 함께 있으면 보통 큰 값이 정가, 작은 값이 할인가
    if len(values) >= 2:
        original = max(values)
        sale = min(values)
    else:
        original = None
        sale = values[0]

    discount_rate = calculate_discount_rate(original, sale)

    return original, sale, discount_rate


def infer_category(raw_title: str) -> str:
    """룰 기반 카테고리 추정.

    - why: 상세 페이지 크롤링 없이도 최소한의 필터링 경험 제공
    """

    normalized = normalize_product_title(raw_title)
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "기타"


def make_slot_hash(channel_id: int, start_at: datetime, normalized_title: str) -> str:
    """슬롯 중복 방지를 위한 해시."""

    base = f"{channel_id}|{start_at.isoformat()}|{normalized_title}".lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
