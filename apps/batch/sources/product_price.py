# why: 상품 상세 페이지에서 정가/할인가 정보를 확보하기 위한 전용 모듈
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from common.config import BatchSettings
from common.normalize import parse_price_text


logger = logging.getLogger("batch.product_price")


SALE_KEYWORDS = {
    "saleprice",
    "sellprice",
    "sellingprice",
    "discountprice",
    "finalprice",
    "price",
}

ORIGINAL_KEYWORDS = {
    "originprice",
    "originalprice",
    "listprice",
    "consumerprice",
    "regularprice",
    "normalprice",
    "wasprice",
}

SALE_LABELS = [
    "할인가",
    "할인판매가",
    "즉시할인가",
    "혜택가",
    "최종가",
    "판매가",
]

ORIGINAL_LABELS = [
    "정가",
    "정상가",
    "소비자가",
    "기준가",
    "기존가",
]

FORCE_BROWSER_HOSTS = {
    "m.gmarket.co.kr",
    "mobile.gmarket.co.kr",
    "item.gmarket.co.kr",
}


class ProductPriceFetcher:
    """상품 상세 페이지에서 가격 정보를 가져오는 헬퍼.

    - why: 상세 페이지는 호출 비용이 크므로 캐시/횟수 제한으로 보호한다.
    """

    def __init__(self, settings: BatchSettings) -> None:
        self.settings = settings
        self.enabled = settings.product_price_fetch_enabled
        self.max_fetch = settings.product_price_fetch_max
        self.user_agent = settings.user_agent
        self.browser_fallback = settings.product_price_fetch_browser_fallback
        self.browser_max = settings.product_price_fetch_browser_max
        self.concurrency = settings.product_price_fetch_concurrency
        self._cache: dict[str, tuple[int | None, int | None]] = {}
        self._count = 0
        self._success = 0
        self._browser_count = 0
        self._browser_skipped = 0
        self._browser_limit_logged = False

    def fetch(self, url: str | None) -> tuple[int | None, int | None] | None:
        if not self.enabled or not url:
            return None

        if url in self._cache:
            return self._cache[url]

        if self._count >= self.max_fetch:
            return None

        try:
            self._count += 1

            # G마켓 계열은 봇 차단 빈도가 높아서 브라우저 렌더링만 사용
            if _should_force_browser(url):
                if not self.browser_fallback:
                    logger.warning("브라우저 비활성화로 G마켓 상품 크롤링 스킵: %s", url)
                    self._cache[url] = (None, None)
                    return self._cache[url]

                if not self._should_use_browser():
                    self._browser_skipped += 1
                    self._log_browser_limit()
                    self._cache[url] = (None, None)
                    return self._cache[url]

                browser_urls = _build_browser_urls(url)
                browser_prices = fetch_product_html_with_browser(
                    browser_urls, self.user_agent, self.settings
                )
                if browser_prices:
                    original_price, sale_price = browser_prices
                    self._cache[url] = (original_price, sale_price)
                    if original_price or sale_price:
                        self._success += 1
                        return self._cache[url]

                # 브라우저로도 실패하면 HTTP 요청은 생략해 시간/차단 로그를 줄인다.
                logger.warning("브라우저 기반 크롤링 실패로 G마켓 상품 스킵: %s", url)
                self._cache[url] = (None, None)
                return self._cache[url]

            html = fetch_product_html(url, self.user_agent)
            if _is_blocked_html(html):
                logger.warning("상품 페이지 차단/빈 응답 감지: %s", url)
                html = ""

            original_price, sale_price = parse_product_price(html)

            if (original_price is None and sale_price is None) and self._should_use_browser():
                browser_urls = _build_browser_urls(url)
                browser_prices = fetch_product_html_with_browser(
                    browser_urls, self.user_agent, self.settings
                )
                if browser_prices:
                    original_price, sale_price = browser_prices

            self._cache[url] = (original_price, sale_price)
            if original_price or sale_price:
                self._success += 1
            return self._cache[url]
        except httpx.HTTPError:
            logger.warning("상품 가격 크롤링 실패: %s", url)
            if self._should_use_browser():
                try:
                    browser_urls = _build_browser_urls(url)
                    browser_prices = fetch_product_html_with_browser(
                        browser_urls, self.user_agent, self.settings
                    )
                    if browser_prices:
                        original_price, sale_price = browser_prices
                        self._cache[url] = (original_price, sale_price)
                        if original_price or sale_price:
                            self._success += 1
                        return self._cache[url]
                except Exception:
                    logger.exception("브라우저 기반 크롤링 실패: %s", url)
        except Exception:
            logger.exception("상품 가격 파싱 중 예외: %s", url)

        self._cache[url] = (None, None)
        return None

    def stats(self) -> dict[str, int]:
        return {
            "requested": self._count,
            "success": self._success,
            "cache_size": len(self._cache),
            "browser_requested": self._browser_count,
            "browser_skipped": self._browser_skipped,
        }

    def _should_use_browser(self) -> bool:
        if not self.browser_fallback:
            return False
        if self.browser_max <= 0:
            self._browser_count += 1
            return True
        if self._browser_count >= self.browser_max:
            return False
        self._browser_count += 1
        return True

    def _log_browser_limit(self) -> None:
        if self.browser_max <= 0:
            return
        if self._browser_limit_logged:
            return
        logger.warning(
            "브라우저 크롤링 한도(%s) 초과로 일부 상품을 스킵합니다.",
            self.browser_max,
        )
        self._browser_limit_logged = True


def fetch_product_html(url: str, user_agent: str) -> str:
    """상품 상세 HTML을 가져온다.

    - why: G마켓 상세 페이지는 간헐적으로 429/5xx를 반환하므로 재시도 적용.
    """

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://mobile.gmarket.co.kr/",
    }

    # 요청 간 랜덤 딜레이 (서비스 부하 완화 목적)
    time.sleep(random.uniform(0.2, 0.5))

    retry = 0
    backoff = 0.5

    while True:
        try:
            with httpx.Client(timeout=6.0, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                if response.status_code == 403:
                    # why: 봇 차단일 가능성이 높아 HTTP 재시도를 중단하고 브라우저로 넘긴다.
                    return ""
                if response.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError(
                        f"temporary error: {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError:
            retry += 1
            if retry > 1:
                raise
            time.sleep(backoff)
            backoff *= 2
        except httpx.HTTPError:
            retry += 1
            if retry > 1:
                raise
            time.sleep(backoff)
            backoff *= 2


def fetch_product_html_with_browser(
    urls: list[str] | str, user_agent: str, settings: BatchSettings
) -> tuple[int | None, int | None] | None:
    """Playwright로 상품 페이지를 렌더링해 가격을 직접 추출.

    - why: JS 렌더링 후에만 노출되는 쿠폰가/정가를 안정적으로 확보하기 위해.
    """

    try:
        # Playwright는 비용이 크므로 필요할 때만 import
        from playwright.sync_api import sync_playwright
    except Exception:
        logger.warning("Playwright가 설치되지 않아 브라우저 크롤링을 건너뜁니다.")
        return None

    url_list = [urls] if isinstance(urls, str) else urls
    storage_state = _resolve_storage_state(settings)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not settings.product_price_playwright_headful,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=user_agent,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={"width": 1280, "height": 720},
            storage_state=storage_state,
        )
        # why: 간단한 자동화 탐지 우회 (navigator.webdriver 제거)
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = context.new_page()
        try:
            for target_url in url_list:
                try:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=8000)
                    # JS 렌더링이 필요한 가격 영역을 잠깐 대기
                    _wait_for_price_selectors(page, timeout_ms=1500)
                    page.wait_for_timeout(300)
                    prices = _extract_prices_from_playwright_page(page)
                    if prices and (prices[0] is not None or prices[1] is not None):
                        return prices

                    html = page.content()
                    if not _is_blocked_html(html):
                        parsed = parse_product_price(html)
                        if parsed and (parsed[0] is not None or parsed[1] is not None):
                            return parsed
                except Exception as exc:
                    logger.warning("브라우저 이동 실패: %s (%s)", target_url, exc)
                    continue
            return None
        finally:
            context.close()
            browser.close()


def parse_product_price(html: str) -> tuple[int | None, int | None]:
    """상품 상세 HTML에서 정가/할인가를 추출.

    - why: 방송 화면에 정가 대비 할인율을 노출하기 위해 정가 정보를 확보.
    """

    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")

    original_candidates: list[int] = []
    sale_candidates: list[int] = []

    # 쿠폰 최종가(할인가)는 가장 우선순위가 높다.
    _extract_from_coupon_price(soup, sale_candidates)
    _extract_from_meta(soup, sale_candidates)
    _extract_from_ld_json(soup, original_candidates, sale_candidates)
    _extract_from_dom_price(soup, original_candidates, sale_candidates)
    _extract_from_original_price_node(soup, original_candidates)
    _extract_from_data_attrs(soup, original_candidates, sale_candidates)
    _extract_from_text(soup.get_text(" ", strip=True), original_candidates, sale_candidates)
    _extract_from_raw_json(html, original_candidates, sale_candidates)

    original = _select_original_price(original_candidates)
    sale = _select_sale_price(sale_candidates)

    if original and sale and original < sale:
        # 왜: 일부 페이지는 sale/original 키가 뒤집혀 있어 안전하게 보정
        original, sale = sale, original

    return original, sale


def _select_original_price(candidates: list[int]) -> int | None:
    filtered = [price for price in candidates if price >= 100]
    return max(filtered) if filtered else None


def _select_sale_price(candidates: list[int]) -> int | None:
    filtered = [price for price in candidates if price >= 100]
    return min(filtered) if filtered else None


def _extract_from_meta(soup: BeautifulSoup, sale_candidates: list[int]) -> None:
    for meta in soup.select(
        'meta[property="product:price:amount"], meta[itemprop="price"], meta[name="price"]'
    ):
        price = parse_price_text(meta.get("content"))
        if price:
            sale_candidates.append(price)


def _extract_from_data_attrs(
    soup: BeautifulSoup, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    for tag in soup.find_all(attrs=True):
        for attr, value in tag.attrs.items():
            if not isinstance(value, str):
                continue

            attr_key = attr.lower()
            if "price" not in attr_key:
                continue

            price = parse_price_text(value)
            if not price:
                continue

            if "original" in attr_key or "origin" in attr_key or "list" in attr_key:
                original_candidates.append(price)
            elif "sale" in attr_key or "sell" in attr_key or "discount" in attr_key:
                sale_candidates.append(price)


def _extract_from_text(text: str, original_candidates: list[int], sale_candidates: list[int]) -> None:
    for label in ORIGINAL_LABELS:
        match = re.search(rf"{label}\s*[:\s]*([0-9][0-9,]*)\s*원", text)
        if match:
            price = parse_price_text(match.group(1))
            if price:
                original_candidates.append(price)

    for label in SALE_LABELS:
        match = re.search(rf"{label}\s*[:\s]*([0-9][0-9,]*)\s*원", text)
        if match:
            price = parse_price_text(match.group(1))
            if price:
                sale_candidates.append(price)


def _extract_from_dom_price(
    soup: BeautifulSoup, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    """DOM 구조에서 가격을 추출.

    - why: '기존가'가 보이는 구조는 텍스트 조합만으로 놓칠 수 있어 DOM 기준으로 탐색.
    """

    for price_box in soup.select("span.text__price, div.text__price, p.text__price"):
        # 기존가 영역은 정가로 처리하므로 여기서는 제외
        if price_box.find_parent(class_="text__price-original"):
            continue
        text = price_box.get_text(" ", strip=True)
        price = parse_price_text(text)
        if not price:
            continue

        # 접근성 텍스트나 주변 문구로 구분
        if any(label in text for label in ORIGINAL_LABELS) or (
            price_box.select_one(".for-a11y")
            and "기존가" in price_box.get_text(" ", strip=True)
        ):
            original_candidates.append(price)
            continue

        if any(label in text for label in SALE_LABELS):
            sale_candidates.append(price)
            continue


def _extract_from_original_price_node(
    soup: BeautifulSoup, original_candidates: list[int]
) -> None:
    """정가 전용 영역(text__price-original)에서 가격 추출."""

    for node in soup.select(".text__price-original .text__price"):
        text = node.get_text(" ", strip=True)
        price = parse_price_text(text)
        if price:
            original_candidates.append(price)


def _extract_from_coupon_price(soup: BeautifulSoup, sale_candidates: list[int]) -> None:
    """쿠폰 적용 최종가 추출.

    - why: 상세 페이지에서 최종가가 별도 클래스(price_real)로 제공됨.
    """

    # 쿠폰 적용 영역 우선 탐색
    coupon_node = soup.select_one(".price_innerwrap-coupon strong.price_real")
    if coupon_node:
        price = parse_price_text(coupon_node.get_text(" ", strip=True))
        if price:
            sale_candidates.append(price)

    # 일반 price_real도 함께 수집 (최소값을 최종가로 사용)
    for node in soup.select("strong.price_real, .price_real"):
        price = parse_price_text(node.get_text(" ", strip=True))
        if price:
            sale_candidates.append(price)


def _extract_prices_from_playwright_page(page) -> tuple[int | None, int | None] | None:
    """Playwright DOM에서 가격을 직접 추출."""

    try:
        sale_text = None
        original_text = None

        coupon_node = page.locator(".price_innerwrap-coupon strong.price_real")
        if coupon_node.count() > 0:
            sale_text = coupon_node.first.text_content()
        else:
            # 쿠폰 영역이 없으면 price_real 전체 중 최소값을 사용
            sale_nodes = page.locator("strong.price_real, .price_real")
            prices: list[int] = []
            for idx in range(sale_nodes.count()):
                text = sale_nodes.nth(idx).text_content()
                price = parse_price_text(text) if text else None
                if price:
                    prices.append(price)
            if prices:
                sale_text = str(min(prices))

        original_node = page.locator(".text__price-original .text__price, .text__price-original")
        if original_node.count() > 0:
            original_text = original_node.first.text_content()

        sale_price = parse_price_text(sale_text) if sale_text else None
        original_price = parse_price_text(original_text) if original_text else None

        if sale_price is None and original_price is None:
            return None

        return (original_price, sale_price)
    except Exception:
        return None


async def _async_extract_prices_from_playwright_page(page) -> tuple[int | None, int | None] | None:
    try:
        sale_text = None
        original_text = None

        coupon_node = page.locator(".price_innerwrap-coupon strong.price_real")
        if await coupon_node.count() > 0:
            sale_text = await coupon_node.first.text_content()
        else:
            sale_nodes = page.locator("strong.price_real, .price_real")
            prices: list[int] = []
            count = await sale_nodes.count()
            for idx in range(count):
                text = await sale_nodes.nth(idx).text_content()
                price = parse_price_text(text) if text else None
                if price:
                    prices.append(price)
            if prices:
                sale_text = str(min(prices))

        original_node = page.locator(".text__price-original .text__price, .text__price-original")
        if await original_node.count() > 0:
            original_text = await original_node.first.text_content()

        sale_price = parse_price_text(sale_text) if sale_text else None
        original_price = parse_price_text(original_text) if original_text else None

        if sale_price is None and original_price is None:
            return None
        return (original_price, sale_price)
    except Exception:
        return None


def _extract_from_ld_json(
    soup: BeautifulSoup, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        _walk_json(data, original_candidates, sale_candidates)


def _extract_from_raw_json(
    html: str, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    """원시 HTML에서 가격 키를 탐색.

    - why: 일부 SPA는 JSON을 그대로 심어두고 있어 DOM 파싱만으로는 누락된다.
    """

    for key in ORIGINAL_KEYWORDS:
        for match in re.finditer(rf'"{key}"\s*:\s*"?([0-9,]+)', html, re.IGNORECASE):
            price = parse_price_text(match.group(1))
            if price:
                original_candidates.append(price)

    for key in SALE_KEYWORDS:
        for match in re.finditer(rf'"{key}"\s*:\s*"?([0-9,]+)', html, re.IGNORECASE):
            price = parse_price_text(match.group(1))
            if price:
                sale_candidates.append(price)


def _walk_json(
    data: Any, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in ORIGINAL_KEYWORDS:
                price = _coerce_price(value)
                if price:
                    original_candidates.append(price)
            if key_lower in SALE_KEYWORDS:
                price = _coerce_price(value)
                if price:
                    sale_candidates.append(price)

            if key_lower == "pricespecification":
                _extract_from_price_spec(value, original_candidates, sale_candidates)

            if key_lower == "offers":
                _walk_json(value, original_candidates, sale_candidates)
            else:
                _walk_json(value, original_candidates, sale_candidates)
    elif isinstance(data, list):
        for item in data:
            _walk_json(item, original_candidates, sale_candidates)


def _extract_from_price_spec(
    spec: Any, original_candidates: list[int], sale_candidates: list[int]
) -> None:
    if isinstance(spec, list):
        for item in spec:
            _extract_from_price_spec(item, original_candidates, sale_candidates)
        return

    if not isinstance(spec, dict):
        return

    price = _coerce_price(spec.get("price"))
    price_type = str(spec.get("priceType", "")).lower()

    if not price:
        return

    if "listprice" in price_type or "original" in price_type or "regular" in price_type:
        original_candidates.append(price)
    elif "sale" in price_type or "discount" in price_type:
        sale_candidates.append(price)
    else:
        # priceType이 없으면 sale로 간주
        sale_candidates.append(price)


def _coerce_price(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):
        return parse_price_text(value)

    return None


def _is_blocked_html(html: str) -> bool:
    if not html:
        return True
    lowered = html.lower()
    return "error404" in lowered or "access denied" in lowered


def _should_force_browser(url: str) -> bool:
    try:
        return any(host in url for host in FORCE_BROWSER_HOSTS)
    except Exception:
        return False


def _wait_for_price_selectors(page, timeout_ms: int) -> None:
    """가격 DOM이 렌더링될 시간을 짧게 확보."""

    for selector in ("strong.price_real", ".price_real", ".text__price-original"):
        try:
            page.wait_for_selector(selector, timeout=timeout_ms)
            return
        except Exception:
            continue


async def _async_wait_for_price_selectors(page, timeout_ms: int) -> None:
    for selector in ("strong.price_real", ".price_real", ".text__price-original"):
        try:
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return
        except Exception:
            continue


def _resolve_storage_state(settings: BatchSettings) -> str | None:
    path = settings.product_price_playwright_storage_state_path
    if not path:
        return None
    expanded = os.path.expanduser(path)
    if os.path.exists(expanded):
        return expanded
    return None


def _extract_goodscode(url: str) -> str | None:
    match = re.search(r"/vi/product/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"goodscode=(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"goodsCode=(\d+)", url)
    if match:
        return match.group(1)
    return None


def _build_browser_urls(url: str) -> list[str]:
    urls = [url]
    goodscode = _extract_goodscode(url)
    if not goodscode:
        return urls

    # G마켓 계열 대체 URL 시도
    urls.extend(
        [
            f"https://m.gmarket.co.kr/Item?goodsCode={goodscode}",
            f"https://m.gmarket.co.kr/Item?goodscode={goodscode}",
            f"https://mobile.gmarket.co.kr/Item?goodscode={goodscode}",
            f"https://item.gmarket.co.kr/Item?goodscode={goodscode}",
            f"https://mitem.gmarket.co.kr/Item?goodscode={goodscode}",
        ]
    )
    return urls


def _build_http_urls(url: str) -> list[str]:
    """HTTP 요청용 대체 URL 목록.

    - why: m.gmarket 계열이 403일 때 item.gmarket 도메인이 열리는 경우가 있음.
    """

    urls: list[str] = []
    goodscode = _extract_goodscode(url)
    if goodscode:
        urls.extend(
            [
                f"https://item.gmarket.co.kr/Item?goodsCode={goodscode}",
                f"https://item.gmarket.co.kr/Item?goodscode={goodscode}",
                f"https://mitem.gmarket.co.kr/Item?goodscode={goodscode}",
                f"https://mobile.gmarket.co.kr/Item?goodscode={goodscode}",
            ]
        )
    urls.append(url)
    return urls


async def fetch_product_prices_batch(
    urls: list[str], settings: BatchSettings
) -> dict[str, tuple[int | None, int | None]]:
    """상품 상세 페이지 가격을 비동기로 병렬 수집.

    - why: 상품 URL이 많을 때 순차 크롤링이 느려 UI 업데이트가 지연됨.
    """

    if not urls:
        return {}

    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://mobile.gmarket.co.kr/",
    }

    timeout = httpx.Timeout(6.0, connect=3.0)
    sem = asyncio.Semaphore(settings.product_price_fetch_concurrency)
    results: dict[str, tuple[int | None, int | None]] = {}

    async def fetch_one(target_url: str) -> None:
        candidate_urls = [target_url]
        if _should_force_browser(target_url):
            # 브라우저 전용 도메인이라도 HTTP 대체 URL을 먼저 시도한다.
            candidate_urls = _build_http_urls(target_url)

        async with sem:
            try:
                async with httpx.AsyncClient(
                    timeout=timeout, headers=headers, follow_redirects=True
                ) as client:
                    for candidate in candidate_urls:
                        resp = await client.get(candidate)
                        if resp.status_code == 403:
                            continue
                        if resp.status_code in (429, 500, 502, 503, 504):
                            continue
                        html = resp.text
                        if _is_blocked_html(html):
                            continue
                        results[target_url] = parse_product_price(html)
                        return
                    results[target_url] = (None, None)
            except Exception:
                results[target_url] = (None, None)

    await asyncio.gather(*(fetch_one(url) for url in urls))
    return results


async def fetch_product_prices_batch_browser(
    urls: list[str], settings: BatchSettings
) -> dict[str, tuple[int | None, int | None]]:
    """브라우저 기반 가격 크롤링을 병렬로 수행.

    - why: G마켓 계열은 403 빈도가 높아 브라우저 기반 크롤링의 병렬화가 필요.
    """

    if not urls or not settings.product_price_fetch_browser_fallback:
        return {}

    target_urls = [url for url in urls if _should_force_browser(url)]
    if not target_urls:
        return {}

    chunk_size = settings.product_price_fetch_browser_max
    if chunk_size <= 0:
        chunk_size = len(target_urls)
    sem = asyncio.Semaphore(settings.product_price_fetch_browser_concurrency)
    results: dict[str, tuple[int | None, int | None]] = {}

    try:
        from playwright.async_api import async_playwright
    except Exception:
        logger.warning("Playwright가 설치되지 않아 브라우저 병렬 크롤링을 건너뜁니다.")
        return {}

    storage_state = _resolve_storage_state(settings)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=not settings.product_price_playwright_headful,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=settings.user_agent,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            viewport={"width": 1280, "height": 720},
            storage_state=storage_state,
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        async def fetch_one(target_url: str) -> None:
            async with sem:
                page = await context.new_page()
                try:
                    candidate_urls = _build_browser_urls(target_url)
                    for candidate in candidate_urls:
                        try:
                            await page.goto(
                                candidate, wait_until="domcontentloaded", timeout=6000
                            )
                            await _async_wait_for_price_selectors(page, timeout_ms=1500)
                            await page.wait_for_timeout(300)
                            prices = await _async_extract_prices_from_playwright_page(page)
                            if prices and (prices[0] is not None or prices[1] is not None):
                                results[target_url] = prices
                                return

                            html = await page.content()
                            if not _is_blocked_html(html):
                                parsed = parse_product_price(html)
                                if parsed and (parsed[0] is not None or parsed[1] is not None):
                                    results[target_url] = parsed
                                    return
                        except Exception as exc:
                            logger.warning(
                                "브라우저 병렬 이동 실패: %s (%s)", candidate, exc
                            )
                            continue
                    results[target_url] = (None, None)
                finally:
                    await page.close()

        deadline = time.monotonic() + settings.product_price_fetch_browser_timeout_sec

        for start in range(0, len(target_urls), chunk_size):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.warning(
                    "브라우저 병렬 크롤링 타임아웃(%s초). 일부 결과만 반영합니다.",
                    settings.product_price_fetch_browser_timeout_sec,
                )
                break

            batch_urls = target_urls[start : start + chunk_size]
            try:
                await asyncio.wait_for(
                    asyncio.gather(*(fetch_one(url) for url in batch_urls)),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "브라우저 병렬 크롤링 타임아웃(%s초). 일부 결과만 반영합니다.",
                    settings.product_price_fetch_browser_timeout_sec,
                )
                break
        await context.close()
        await browser.close()

    return results
