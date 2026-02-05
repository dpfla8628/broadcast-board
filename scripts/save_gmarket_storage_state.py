"""G마켓 접속용 Playwright storage_state 저장.

왜 필요한가:
- G마켓은 봇 차단이 있어 세션/쿠키가 없으면 403이 빈번합니다.
- 한번 사람처럼 접속해 storage_state를 저장하면 이후 크롤링에 재사용할 수 있습니다.
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

DEFAULT_STATE = "./apps/batch/.playwright/storage_state.json"


def main() -> None:
    state_path = os.environ.get("PRODUCT_PRICE_PLAYWRIGHT_STORAGE_STATE_PATH", DEFAULT_STATE)
    state_file = Path(state_path).expanduser().resolve()
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul")
        page = context.new_page()
        print("브라우저가 열리면 G마켓에 로그인/인증을 완료하세요.")
        page.goto("https://m.gmarket.co.kr", wait_until="domcontentloaded")
        input("완료되면 Enter를 눌러 storage_state를 저장합니다...")
        context.storage_state(path=str(state_file))
        context.close()
        browser.close()

    print(f"저장 완료: {state_file}")


if __name__ == "__main__":
    main()
