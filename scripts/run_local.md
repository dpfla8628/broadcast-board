# 로컬 실행 순서

1. DB 세팅
   - `scripts/setup_local_mysql.md` 참고

2. API 마이그레이션
   - `cd apps/api`
   - `alembic upgrade head`

3. 배치 실행 (편성표 수집)
   - `cd apps/batch`
   - `python -m batch.main fetch_schedule`

3-1. (선택) 라이브 스트림 자동 수집
   - `cd apps/batch`
   - `python -m batch.main sync_live_streams`
   - 최초 1회 `playwright install` 필요
   - 참고: 현재 UI는 LIVE 클릭 시 채널 라이브 페이지로 바로 이동합니다.

4. API 실행
   - `cd apps/api`
   - `uvicorn app.main:app --reload --port 8000`

5. 웹 실행
   - `cd apps/web`
   - `npm install`
   - `npm run dev`

---

## 한 번에 마이그레이션 + 재시작

- 아래 스크립트는 마이그레이션 적용 후 API/웹을 자동 재시작합니다.
- 주의: 이미 떠 있는 프로세스가 있으면 포트(8000/3000/3001) 기준으로 종료합니다.

```
bash scripts/dev_refresh.sh
```

로그 확인:
- API: `scripts/dev_api.log`
- WEB: `scripts/dev_web.log`
