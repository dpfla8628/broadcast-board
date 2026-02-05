#!/usr/bin/env bash
set -euo pipefail

# why: 마이그레이션 + API/웹 재시작을 한 번에 처리해 운영 실수를 줄이기 위함

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BATCH_ASYNC="${BATCH_ASYNC:-1}"

echo "[0/4] 편성표 재수집"
if [[ "${BATCH_ASYNC}" == "1" ]]; then
  (
    cd "${ROOT_DIR}/apps/batch"
    nohup /Users/yerimlee/.pyenv/versions/3.12.7/bin/python -m batch.main fetch_schedule \
      > "${ROOT_DIR}/scripts/dev_batch.log" 2>&1 &
    echo " - 배치 백그라운드 실행 (pid: $!)"
    echo " - 로그: ${ROOT_DIR}/scripts/dev_batch.log"
  )
else
  (
    cd "${ROOT_DIR}/apps/batch"
    /Users/yerimlee/.pyenv/versions/3.12.7/bin/python -m batch.main fetch_schedule \
      | tee "${ROOT_DIR}/scripts/dev_batch.log"
  )
fi

echo "[1/4] Alembic 마이그레이션 적용"
(
  cd "${ROOT_DIR}/apps/api"
  alembic upgrade head
)

echo "[2/4] 기존 API/웹 프로세스 정리"
for port in 8000 3000 3001; do
  pid="$(lsof -ti tcp:${port} || true)"
  if [[ -n "${pid}" ]]; then
    echo " - 포트 ${port} 사용중인 프로세스 종료 (pid: ${pid})"
    kill "${pid}" || true
  fi
done

sleep 1

echo "[3/4] API 재시작 (포트 8000)"
(
  cd "${ROOT_DIR}/apps/api"
  nohup uvicorn app.main:app --reload --port 8000 > "${ROOT_DIR}/scripts/dev_api.log" 2>&1 &
)

echo "[4/4] Web 재시작 (포트 3000)"
(
  cd "${ROOT_DIR}/apps/web"
  if [[ ! -d "node_modules/hls.js" ]]; then
    echo " - 의존성 설치 (hls.js 포함)"
    npm install
  fi
  nohup npm run dev -- --port 3000 > "${ROOT_DIR}/scripts/dev_web.log" 2>&1 &
)

echo "완료: API http://localhost:8000 / WEB http://localhost:3000"
