# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_value, is_invalid_token
from app.core.errors import AppError
from app.repositories.alert_repo import AlertRepository
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertService:
    """알림 규칙 서비스 계층."""

    def __init__(self) -> None:
        self.repo = AlertRepository()

    def list_alerts(self, db: Session):
        alerts = self.repo.list_alerts(db)
        return [self._decrypt_alert(alert) for alert in alerts]

    def create_alert(self, db: Session, payload: AlertCreate):
        alert = self.repo.create_alert(db, payload)
        return self._decrypt_alert(alert)

    def update_alert(self, db: Session, alert_id: int, payload: AlertUpdate):
        alert = self.repo.get_alert(db, alert_id)
        if not alert:
            raise AppError(status_code=404, message="알림 규칙을 찾을 수 없습니다.", code="NOT_FOUND")
        updated = self.repo.update_alert(db, alert, payload)
        return self._decrypt_alert(updated)

    def delete_alert(self, db: Session, alert_id: int):
        alert = self.repo.get_alert(db, alert_id)
        if not alert:
            raise AppError(status_code=404, message="알림 규칙을 찾을 수 없습니다.", code="NOT_FOUND")
        self.repo.delete_alert(db, alert)
        return True

    def _decrypt_alert(self, alert):
        try:
            alert.destination_value = decrypt_value(alert.destination_value)
            return alert
        except Exception as exc:
            if is_invalid_token(exc):
                # 기존 평문 데이터가 있을 수 있으므로, 안전하게 평문을 그대로 반환
                return alert
            raise
