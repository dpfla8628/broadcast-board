# why: 라이브 스트림(HLS) URL을 자동 수집하기 위한 Playwright 기반 수집기
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from common.config import get_batch_settings


logger = logging.getLogger("batch.live_streams")


STREAM_URL_PATTERNS: dict[str, list[str]] = {
    # 아래 패턴은 예시 기반이며, 필요 시 추가/수정 가능합니다.
    "cjon": ["cjonstyle", "cjmalllive"],
    "gsshop": ["gsshop.com", "gsshop_hd", "gstv-gsshop"],
    # 쇼핑엔티/기타는 실제 도메인 확인 후 수정 필요
    "shoppingnt": ["wshopping", "catenoid", "w-shopping"],
}


@dataclass
class StreamItem:
    url: str
    context_text: str | None = None


@dataclass
class StreamCollectResult:
    matched: dict[str, str]
    unmapped: list[str]
    items: list[StreamItem]


def _collect_m3u8_from_page(url: str) -> list[StreamItem]:
    items_by_url: dict[str, StreamItem] = {}

    # why: playwright는 선택적 의존성이므로 필요할 때만 import
    from playwright.sync_api import sync_playwright

    def handle_response(response):
        if ".m3u8" in response.url:
            items_by_url.setdefault(response.url, StreamItem(url=response.url))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=get_batch_settings().user_agent)
        page.on("response", handle_response)
        page.goto(url, wait_until="networkidle", timeout=60_000)

        # 동적 로딩 시간을 고려해 약간 대기
        page.wait_for_timeout(3_000)

        # DOM에서 직접 확인되는 source도 수집
        dom_items: list[dict] = page.eval_on_selector_all(
            "video",
            """elements => elements.map(el => {
              const sourceEl = el.querySelector('source');
              const src = sourceEl?.getAttribute('src') || el.getAttribute('src') || '';
              const container = el.closest('li, article, section, div');
              const text = container ? container.innerText : '';
              return { src, text };
            }).filter(item => item.src)""",
        )
        for item in dom_items:
            src = item.get("src") or ""
            if ".m3u8" not in src:
                continue
            if src in items_by_url:
                # 기존에 수집된 항목이면 컨텍스트만 보강
                if item.get("text"):
                    items_by_url[src].context_text = item["text"]
            else:
                items_by_url[src] = StreamItem(url=src, context_text=item.get("text"))

        browser.close()

    return sorted(items_by_url.values(), key=lambda item: item.url)


def _match_streams(items: Iterable[StreamItem], channel_name_map: dict[str, str]) -> StreamCollectResult:
    matched: dict[str, str] = {}
    unmapped: list[str] = []

    for item in items:
        url_lower = item.url.lower()
        found = False

        # 1) 도메인/패턴 기반 매칭
        for channel_code, patterns in STREAM_URL_PATTERNS.items():
            if any(pattern.lower() in url_lower for pattern in patterns):
                matched.setdefault(channel_code, item.url)
                found = True
                break

        # 2) 페이지 컨텍스트에서 채널명 매칭
        if not found and item.context_text:
            for channel_name, channel_code in channel_name_map.items():
                if channel_name and channel_name in item.context_text:
                    matched.setdefault(channel_code, item.url)
                    found = True
                    break

        if not found:
            unmapped.append(item.url)

    return StreamCollectResult(matched=matched, unmapped=unmapped, items=list(items))


def collect_live_streams(channel_name_map: dict[str, str]) -> StreamCollectResult:
    settings = get_batch_settings()
    logger.info("라이브 스트림 수집 시작: %s", settings.live_stream_schedule_url)

    items = _collect_m3u8_from_page(settings.live_stream_schedule_url)
    if not items:
        logger.warning("수집된 스트림 URL이 없습니다. 페이지 로딩/셀렉터를 확인하세요.")

    result = _match_streams(items, channel_name_map)
    logger.info("스트림 매칭 완료: matched=%s, unmapped=%s", len(result.matched), len(result.unmapped))

    _write_report(result)
    return result


def _write_report(result: StreamCollectResult) -> None:
    report_dir = Path(__file__).resolve().parents[1] / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "live_streams_report.json"

    report_path.write_text(
        json.dumps(
            {
                "matched": result.matched,
                "unmapped": result.unmapped,
                "items": [item.__dict__ for item in result.items],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("리포트 저장: %s", report_path)
