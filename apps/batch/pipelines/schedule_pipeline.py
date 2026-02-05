# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from datetime import datetime
import asyncio
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.config import get_batch_settings
from common.models import BroadcastSlot, BroadcastStatus, Channel
from common.normalize import (
    calculate_discount_rate,
    infer_category,
    make_slot_hash,
    normalize_product_title,
    parse_price_info,
)
from common.models import BroadcastPriceHistory
from parsers.gmarket_schedule_parser import parse_schedule
from sources.gmarket_schedule import fetch_schedule_html, extract_vendor_list
from sources.product_price import (
    ProductPriceFetcher,
    fetch_product_prices_batch,
    fetch_product_prices_batch_browser,
)


logger = logging.getLogger("batch.schedule")


CHANNEL_CODE_MAP = {
    "롯데홈쇼핑": "lotte",
    "롯데원티비": "lotte_one",
    "현대홈쇼핑": "hyundai",
    "GS SHOP": "gsshop",
    "홈앤쇼핑": "hnsmall",
    "공영쇼핑": "gongs",
    "NS홈쇼핑": "ns",
    "CJ온스타일": "cjon",
    "CJ온스타일+": "cjon_plus",
    "신세계라이브": "ssg_live",
    "쇼핑엔티": "shoppingnt",
    "KT알파쇼핑": "ktalpha",
    "SK스토아": "skstoa",
}

# G마켓 편성표에서 제공하는 라이브 플레이어 링크(BroadcastLayer)를 사용
# why: 미니샵은 상품 탐색용이므로 LIVE 버튼은 실제 라이브 페이지로 연결해야 함
LIVE_LAYER_BASE_URL = "https://mobile.gmarket.co.kr/HomeShopping/BroadcastLayer?compId="
LIVE_COMP_ID_MAP = {
    "gsshop": "gsshoplive",
    "hnsmall": "oshopping",
    "hyundai": "hhome01",
    "ktalpha": "kthshop",
    "lotte": "lotteotv",
    "lotte_one": "lotteotv",
    "ns": "nsmalltv",
    "gongs": "publichstv",
    "shoppingnt": "shpnt1",
    "skstoa": "skstoa",
    "ssg_live": "ssgtvgmkt",
}
CHANNEL_LIVE_URL_MAP = {
    code: f"{LIVE_LAYER_BASE_URL}{comp_id}"
    for code, comp_id in LIVE_COMP_ID_MAP.items()
}

# 특정 채널은 G마켓 라이브 페이지가 아닌 공식 TV 편성표 페이지로 바로 이동
# why: BroadcastLayer가 네트워크 오류로 차단되는 경우가 있어 대체 링크를 우선 사용
CHANNEL_LIVE_URL_OVERRIDE = {
    "skstoa": "https://www.skstoa.com/tv_schedule",
}

# 홈쇼핑 라이브 스트림(HLS) URL 매핑 (필요 시 수동 보강)
# why: LIVE 클릭 시 실제 영상이 재생되도록 HLS 스트림을 우선 사용
CHANNEL_STREAM_URL_MAP = {
    # CJ온스타일
    "cjon": "https://live-ch1.cjonstyle.net/cjmalllive/_definst_/stream2/playlist.m3u8",
    # GS SHOP
    "gsshop": "http://gstv-gsshop.gsshop.com/gsshop_hd/_definst_/gsshop_hd.stream/playlist.m3u8",
    # 쇼핑엔티(매핑 확인 필요 시 수정)
    "shoppingnt": "http://liveout.catenoid.net/live-05-wshopping/wshopping_1500k/playlist.m3u8",
}


def _normalize_channel_code(channel_name: str) -> str:
    # 알 수 없는 채널은 영문/숫자만 남겨 간단한 코드로 변환
    mapped = CHANNEL_CODE_MAP.get(channel_name)
    if mapped:
        return mapped

    sanitized = re.sub(r"[^0-9a-zA-Z]+", "", channel_name).lower()
    return sanitized or "unknown"


def ensure_channel(
    db: Session, channel_code: str, channel_name: str, logo_url: str | None = None
) -> Channel:
    """채널이 없으면 생성.

    - why: 크롤링 소스가 늘어나면 자동으로 채널이 준비되어야 함.
    """

    channel = db.execute(select(Channel).where(Channel.channel_code == channel_code)).scalar_one_or_none()
    live_url = CHANNEL_LIVE_URL_OVERRIDE.get(channel_code) or CHANNEL_LIVE_URL_MAP.get(
        channel_code
    )
    stream_url = CHANNEL_STREAM_URL_MAP.get(channel_code)

    if channel:
        # live URL이 없거나 변경되면 업데이트
        if live_url and channel.channel_live_url != live_url:
            channel.channel_live_url = live_url
        if stream_url and channel.channel_stream_url != stream_url:
            channel.channel_stream_url = stream_url
        if logo_url and channel.channel_logo_url != logo_url:
            channel.channel_logo_url = logo_url
        db.commit()
        db.refresh(channel)
        return channel

    channel = Channel(
        channel_code=channel_code,
        channel_name=channel_name,
        channel_live_url=live_url,
        channel_stream_url=stream_url,
        channel_logo_url=logo_url,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


def resolve_status(start_at: datetime, end_at: datetime) -> BroadcastStatus:
    now = datetime.utcnow()
    if start_at > now:
        return BroadcastStatus.SCHEDULED
    if start_at <= now <= end_at:
        return BroadcastStatus.LIVE
    return BroadcastStatus.ENDED


def upsert_slots(
    db: Session,
    channel: Channel,
    source_code: str,
    items: list[dict],
    price_fetcher: ProductPriceFetcher | None = None,
    price_map: dict[str, tuple[int | None, int | None]] | None = None,
) -> tuple[int, int]:
    """슬롯 업서트 처리.

    - return: (created_count, updated_count)
    """

    created = 0
    updated = 0

    seen_hashes: set[str] = set()

    for item in items:
        normalized_title = normalize_product_title(item["raw_title"])
        category = infer_category(item["raw_title"])
        slot_hash = make_slot_hash(channel.id, item["start_at"], normalized_title)
        original_price, sale_price, discount_rate = parse_price_info(item.get("price_text"))

        if price_map and item.get("product_url") in price_map:
            mapped_original, mapped_sale = price_map[item.get("product_url")]

            if mapped_sale is not None:
                # 쿠폰/최종가는 방송 화면가보다 낮을 수 있으므로 우선 반영
                if sale_price is None or mapped_sale < sale_price:
                    sale_price = mapped_sale

            if mapped_original is not None:
                if original_price is None or mapped_original > original_price:
                    original_price = mapped_original

        if price_fetcher and item.get("product_url") and (
            original_price is None or sale_price is None
        ):
            fetched = price_fetcher.fetch(item.get("product_url"))
            if fetched:
                fetched_original, fetched_sale = fetched

                # 쿠폰/최종가는 방송 화면가보다 낮을 수 있으므로 우선 반영
                if fetched_sale is not None:
                    if sale_price is None or fetched_sale < sale_price:
                        sale_price = fetched_sale

                # 정가 정보가 비어있거나 더 큰 값이 있으면 갱신
                if fetched_original is not None and (
                    original_price is None or fetched_original > original_price
                ):
                    original_price = fetched_original

                # 상세 페이지에 정가만 있는 경우, 방송가보다 큰 값이면 정가로 간주
                if (
                    original_price is None
                    and fetched_sale is not None
                    and sale_price is not None
                    and fetched_sale >= int(sale_price * 1.05)
                ):
                    original_price = fetched_sale

        # 정가가 할인가보다 작으면 뒤집힘을 방지
        if original_price is not None and sale_price is not None and original_price < sale_price:
            original_price, sale_price = sale_price, original_price

        discount_rate = calculate_discount_rate(original_price, sale_price)

        if slot_hash in seen_hashes:
            # 동일한 페이지 내 중복 항목은 스킵
            continue
        seen_hashes.add(slot_hash)

        existing = db.execute(
            select(BroadcastSlot).where(BroadcastSlot.slot_hash == slot_hash)
        ).scalar_one_or_none()

        if existing:
            existing.end_at = item["end_at"]
            existing.raw_title = item["raw_title"]
            existing.normalized_title = normalized_title
            existing.category = category
            existing.product_url = item.get("product_url")
            existing.live_url = item.get("live_url")
            existing.sale_price = sale_price
            existing.original_price = original_price
            existing.discount_rate = discount_rate
            existing.price_text = item.get("price_text")
            existing.image_url = item.get("image_url")
            existing.status = resolve_status(item["start_at"], item["end_at"])
            updated += 1

            _record_price_history(db, existing.id, sale_price, original_price, discount_rate)
        else:
            new_slot = BroadcastSlot(
                channel_id=channel.id,
                source_code=source_code,
                start_at=item["start_at"],
                end_at=item["end_at"],
                raw_title=item["raw_title"],
                normalized_title=normalized_title,
                category=category,
                product_url=item.get("product_url"),
                live_url=item.get("live_url"),
                sale_price=sale_price,
                original_price=original_price,
                discount_rate=discount_rate,
                price_text=item.get("price_text"),
                image_url=item.get("image_url"),
                status=resolve_status(item["start_at"], item["end_at"]),
                slot_hash=slot_hash,
            )
            db.add(new_slot)
            db.flush()
            _record_price_history(db, new_slot.id, sale_price, original_price, discount_rate)
            created += 1

    db.commit()
    return created, updated


def _record_price_history(
    db: Session, slot_id: int, sale_price: int | None, original_price: int | None, discount_rate: float | None
) -> None:
    if not slot_id:
        return

    last = (
        db.query(BroadcastPriceHistory)
        .filter(BroadcastPriceHistory.broadcast_slot_id == slot_id)
        .order_by(BroadcastPriceHistory.collected_at.desc())
        .first()
    )

    if last and last.sale_price == sale_price and last.original_price == original_price:
        return

    history = BroadcastPriceHistory(
        broadcast_slot_id=slot_id,
        collected_at=datetime.utcnow(),
        sale_price=sale_price,
        original_price=original_price,
        discount_rate=discount_rate,
    )
    db.add(history)


def run_schedule_pipeline(db: Session):
    """편성표 수집 파이프라인 전체 실행."""

    source_code = "gmarket_schedule"
    settings = get_batch_settings()
    price_fetcher = ProductPriceFetcher(settings)

    html = fetch_schedule_html()
    vendors = extract_vendor_list(html)

    grouped: dict[str, list[dict]] = {}
    channel_names: dict[str, str] = {}
    channel_logos: dict[str, str | None] = {}

    if vendors:
        # 채널별로 편성표를 재요청하여 전체 방송사를 누락 없이 수집
        for vendor in vendors:
            vendor_url = (
                vendor["href"]
                if vendor["href"].startswith("http")
                else f"https://mobile.gmarket.co.kr{vendor['href']}"
            )
            vendor_html = fetch_schedule_html(vendor_url)
            items = parse_schedule(vendor_html)
            if not items:
                continue

            channel_name = vendor.get("channel_name") or vendor.get("company_id")
            channel_code = _normalize_channel_code(channel_name)
            channel_names[channel_code] = channel_name
            channel_logos[channel_code] = vendor.get("logo_url")

            for item in items:
                item["channel_name"] = channel_name
                grouped.setdefault(channel_code, []).append(item)
    else:
        # fallback: 전체 페이지 파싱
        items = parse_schedule(html)

        if not items:
            logger.warning("파싱 결과가 비어 있습니다. HTML 구조를 확인하세요.")
            return

        for item in items:
            channel_name = item.get("channel_name") or "G마켓"
            channel_code = _normalize_channel_code(channel_name)
            channel_names[channel_code] = channel_name
            grouped.setdefault(channel_code, []).append(item)

    created_total = 0
    updated_total = 0
    price_map: dict[str, tuple[int | None, int | None]] = {}

    if settings.product_price_fetch_enabled:
        product_urls = [
            item.get("product_url")
            for items in grouped.values()
            for item in items
            if item.get("product_url")
        ]
        # 중복 제거
        product_urls = list(dict.fromkeys(product_urls))
        if product_urls:
            try:
                price_map = asyncio.run(fetch_product_prices_batch(product_urls, settings))
            except RuntimeError:
                # 이미 이벤트 루프가 있을 때를 대비한 fallback
                loop = asyncio.new_event_loop()
                price_map = loop.run_until_complete(fetch_product_prices_batch(product_urls, settings))
                loop.close()

            # 브라우저 fallback 병렬 처리 (G마켓 계열만)
            missing_urls = [
                url
                for url in product_urls
                if url and (url not in price_map or price_map[url] == (None, None))
            ]
            if missing_urls and settings.product_price_fetch_browser_fallback:
                try:
                    browser_map = asyncio.run(
                        fetch_product_prices_batch_browser(missing_urls, settings)
                    )
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    browser_map = loop.run_until_complete(
                        fetch_product_prices_batch_browser(missing_urls, settings)
                    )
                    loop.close()
                if browser_map:
                    price_map.update(browser_map)

    for channel_code, channel_items in grouped.items():
        channel = ensure_channel(
            db,
            channel_code=channel_code,
            channel_name=channel_names.get(channel_code, channel_code),
            logo_url=channel_logos.get(channel_code),
        )
        created, updated = upsert_slots(
            db, channel, source_code, channel_items, price_fetcher, price_map
        )
        created_total += created
        updated_total += updated

    if price_fetcher:
        price_stats = price_fetcher.stats()
        logger.info(
            "상품 가격 크롤링 통계: requested=%s success=%s cache=%s browser=%s skipped=%s",
            price_stats["requested"],
            price_stats["success"],
            price_stats["cache_size"],
            price_stats["browser_requested"],
            price_stats.get("browser_skipped", 0),
        )

    logger.info(
        "편성표 수집 완료. created=%s updated=%s total=%s",
        created_total,
        updated_total,
        len(items),
    )
