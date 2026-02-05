# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import HTTPException


class AppError(HTTPException):
    """공통 에러 클래스.

    - why: 에러 포맷을 통일하기 위해 HTTPException을 상속.
    """

    def __init__(self, status_code: int, message: str, code: str = "APP_ERROR"):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
