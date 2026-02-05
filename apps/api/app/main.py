# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.routes.alert_routes import router as alert_router
from app.routes.broadcast_routes import router as broadcast_router
from app.routes.channel_routes import router as channel_router


settings = get_settings()

app = FastAPI(title=settings.app_name)

# CORS는 로컬 개발 환경에서 프론트와 API가 포트를 달리 사용하는 문제를 해결하기 위해 필요.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 모든 커스텀 에러를 동일한 구조로 반환해 프론트 처리 단순화
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "meta": {
                "message": exc.detail.get("message"),
                "code": exc.detail.get("code"),
                "time_policy": settings.time_policy,
            },
        },
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "data": None,
            "meta": {
                "message": "요청 값이 올바르지 않습니다.",
                "code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "time_policy": settings.time_policy,
            },
        },
    )


@app.exception_handler(HTTPException)
def handle_http_exception(request: Request, exc: HTTPException):
    # FastAPI 기본 예외도 동일 포맷으로 감싸 프론트 로직을 단순화
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "meta": {
                "message": str(exc.detail),
                "code": "HTTP_EXCEPTION",
                "time_policy": settings.time_policy,
            },
        },
    )


@app.get("/api/v1/health")
def health_check():
    return {"data": {"status": "ok"}, "meta": {"time_policy": settings.time_policy}}


app.include_router(channel_router)
app.include_router(broadcast_router)
app.include_router(alert_router)
