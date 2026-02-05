# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate
from app.schemas.common import ApiResponse, ResponseMeta
from app.services.alert_service import AlertService


router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])
service = AlertService()
settings = get_settings()


@router.get("", response_model=ApiResponse[list[AlertOut]])
def list_alerts(db: Session = Depends(get_db)):
    alerts = service.list_alerts(db)
    return ApiResponse(
        data=alerts,
        meta=ResponseMeta(count=len(alerts), time_policy=settings.time_policy),
    )


@router.post("", response_model=ApiResponse[AlertOut])
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    alert = service.create_alert(db, payload)
    return ApiResponse(
        data=alert,
        meta=ResponseMeta(message="created", time_policy=settings.time_policy),
    )


@router.patch("/{alert_id}", response_model=ApiResponse[AlertOut])
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)):
    alert = service.update_alert(db, alert_id, payload)
    return ApiResponse(
        data=alert,
        meta=ResponseMeta(message="updated", time_policy=settings.time_policy),
    )


@router.delete("/{alert_id}", response_model=ApiResponse[dict])
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    service.delete_alert(db, alert_id)
    return ApiResponse(
        data={"deleted": True},
        meta=ResponseMeta(message="deleted", time_policy=settings.time_policy),
    )
