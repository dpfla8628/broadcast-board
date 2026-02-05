# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
import random
import time
from typing import Optional
from urllib.parse import urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup

from common.config import get_batch_settings


def fetch_schedule_html(url: Optional[str] = None) -> str:
    """편성표 HTML을 가져온다.

    - why: 실제 크롤링 대상이 1개라면 fetcher 로직을 단순하게 유지하는 것이 유지보수에 유리.
    """

    settings = get_batch_settings()
    target_url = url or settings.schedule_source_url

    headers = {"User-Agent": settings.user_agent}

    # 요청 간 랜덤 딜레이 (서비스 부하 완화 목적)
    time.sleep(random.uniform(0.3, 1.0))

    retry = 0
    backoff = 1.0

    while True:
        try:
            with httpx.Client(timeout=10.0, headers=headers) as client:
                response = client.get(target_url)
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
            if retry > 3:
                raise
            time.sleep(backoff)
            backoff *= 2
        except httpx.HTTPError:
            retry += 1
            if retry > 3:
                raise
            time.sleep(backoff)
            backoff *= 2


def extract_vendor_list(html: str) -> list[dict]:
    """G마켓 편성표 상단의 채널/벤더 목록 추출.

    - why: 채널별 편성표 URL을 확보해 전체 채널을 누락 없이 수집하기 위함.
    """

    soup = BeautifulSoup(html, "html.parser")
    vendors: list[dict] = []

    for link in soup.select("div.list--broadcast_vendors a.link"):
        href = link.get("href") or ""
        if "companyId=" not in href:
            continue

        query = parse_qs(urlparse(href).query)
        company_id = query.get("companyId", [None])[0]
        if not company_id:
            continue

        channel_name = link.get("data-selected-channel-text")
        if not channel_name:
            text_span = link.select_one(".text")
            channel_name = text_span.get_text(strip=True) if text_span else None

        logo_url = link.get("data-selected-channel-image")
        if not logo_url:
            img = link.select_one("img")
            logo_url = img.get("src") if img else None

        vendors.append(
            {
                "company_id": company_id,
                "channel_name": channel_name,
                "logo_url": logo_url,
                "href": href,
            }
        )

    return vendors
