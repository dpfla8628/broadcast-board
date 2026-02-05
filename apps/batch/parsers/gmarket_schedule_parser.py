# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime, timedelta, timezone
import re
from bs4 import BeautifulSoup


TIME_PATTERN = re.compile(r"(오전|오후)\s*(\d{1,2}):(\d{2})")
ISO_TIME_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T")


def _parse_kst_datetime(today_kst_date, meridiem: str, hour: int, minute: int) -> datetime:
    # KST(UTC+9) 기준 시간을 UTC로 변환해 저장
    if meridiem == "오전":
        hour = 0 if hour == 12 else hour
    else:
        # 오후 1시는 13시가 되어야 하므로 12시를 더해준다.
        hour = 12 if hour == 12 else hour + 12

    kst = timezone(timedelta(hours=9))
    dt_kst = datetime(
        today_kst_date.year,
        today_kst_date.month,
        today_kst_date.day,
        hour,
        minute,
        tzinfo=kst,
    )
    return dt_kst.astimezone(timezone.utc).replace(tzinfo=None)


def _extract_channel_from_text(text: str) -> str | None:
    # "(현대홈쇼핑)" 같은 패턴이 있으면 채널명으로 사용
    match = re.search(r"\(([^)]+)\)", text)
    if match:
        return match.group(1).strip()
    return None


def _parse_kst_iso_datetime(value: str) -> datetime | None:
    # data-start-time/data-end-time 은 KST(+09:00) ISO 형태로 제공된다.
    if not value or not ISO_TIME_PATTERN.search(value):
        return None

    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone(timedelta(hours=9)))
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _extract_title_from_description(text: str, price_text: str | None) -> str:
    # 가격/잡음을 제거해 제목만 추정
    title = text
    if price_text:
        title = title.replace(price_text, "")
    title = re.sub(r"\b[0-9][0-9,]*\s*원\b", "", title)
    title = title.replace("홈쇼핑특가", "")
    title = title.replace("관심상품으로 등록", "")
    title = title.replace("관심상품", "")
    title = title.replace("알림설정", "")
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def parse_schedule(html: str) -> list[dict]:
    """G마켓 모바일 홈쇼핑 편성표 파서.

    - why: 실제 HTML은 변할 수 있으므로, 파서 결과를 표준 dict로 만들어 파이프라인을 안정화.
    - 반환 값 예시:
      {
        "start_at": datetime(UTC),
        "end_at": datetime(UTC),
        "raw_title": "...",
        "price_text": "12,900원",
        "image_url": "...",
        "product_url": "...",
        "channel_name": "...",
      }
    """

    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []
    seen: set[tuple[datetime, str]] = set()
    base_url = "https://mobile.gmarket.co.kr"

    # 편성표는 KST 기준으로 노출되므로 KST 날짜를 사용
    today_kst = datetime.now(timezone(timedelta(hours=9))).date()

    # 1) 구조화된 live/now 카드 우선 파싱 (data-start-time 제공)
    for card in soup.select("li[data-start-time]"):
        start_at = _parse_kst_iso_datetime(card.get("data-start-time"))
        end_at = _parse_kst_iso_datetime(card.get("data-end-time") or "")
        if not start_at:
            continue
        if not end_at:
            end_at = start_at + timedelta(hours=1)

        channel_name = None
        vendor = card.select_one(".box--vendor_information .text")
        if vendor:
            channel_name = vendor.get_text(strip=True)

        price_text = None
        price_box = card.select_one(".box--price")
        if price_box:
            price_digits = re.search(r"\d[\d,]*", price_box.get_text(" ", strip=True))
            if price_digits:
                price_text = f"{price_digits.group(0)}원"

        desc = card.select_one(".box--item_description")
        desc_text = desc.get_text(" ", strip=True) if desc else card.get_text(" ", strip=True)
        raw_title = _extract_title_from_description(desc_text, price_text)

        product_url = None
        live_url = None
        image_url = None

        for link in card.find_all("a", href=True):
            href = link.get("href")
            if not href:
                continue
            if "BroadcastLayer?compId=" in href:
                live_url = href if href.startswith("http") else f"{base_url}{href}"
            elif "/vi/product/" in href or "/Item" in href:
                product_url = href if href.startswith("http") else f"{base_url}{href}"

        thumb = card.select_one(".thumbnail")
        if thumb and thumb.has_attr("style"):
            match = re.search(r"url\\(([^)]+)\\)", thumb["style"])
            if match:
                image_url = match.group(1).strip().strip("'\"")

        key = (start_at, raw_title)
        if key in seen:
            continue
        seen.add(key)

        items.append(
            {
                "start_at": start_at,
                "end_at": end_at,
                "raw_title": raw_title,
                "price_text": price_text,
                "image_url": image_url,
                "product_url": product_url,
                "live_url": live_url,
                "channel_name": channel_name,
            }
        )

    # 2) 일반 타임라인 텍스트 파싱 (오전/오후 표기)
    for link in soup.find_all("a"):
        text = link.get_text(" ", strip=True)
        match = TIME_PATTERN.search(text)
        if not match:
            continue

        meridiem, hour_text, minute_text = match.groups()
        start_at = _parse_kst_datetime(
            today_kst, meridiem, int(hour_text), int(minute_text)
        )

        # 종료 시간 정보가 없으므로 1시간 단위로 임시 설정
        end_at = start_at + timedelta(hours=1)

        remainder = text[match.end():].strip()
        price_match = re.search(r"^(.*?)\s*(\d[\d,]*)\s*원", remainder)
        if price_match:
            raw_title = price_match.group(1).strip()
            price_text = f"{price_match.group(2)}원"
        else:
            raw_title = remainder
            price_text = None

        channel_name = _extract_channel_from_text(text)

        # 채널 링크가 있으면 우선 사용
        parent = link.find_parent()
        if parent:
            channel_link = parent.find(
                "a", href=re.compile(r"minishop\.gmarket\.co\.kr")
            )
            if channel_link:
                channel_name = channel_link.get_text(strip=True) or channel_name

        href = link.get("href")
        live_url = None
        product_url = None

        if href:
            if "BroadcastLayer?compId=" in href:
                live_url = href if href.startswith("http") else f"{base_url}{href}"
            else:
                product_url = href if href.startswith("http") else f"{base_url}{href}"

        key = (start_at, raw_title)
        if key in seen:
            continue
        seen.add(key)

        items.append(
            {
                "start_at": start_at,
                "end_at": end_at,
                "raw_title": raw_title,
                "price_text": price_text,
                "image_url": None,
                "product_url": product_url,
                "live_url": live_url,
                "channel_name": channel_name,
            }
        )

    return items
