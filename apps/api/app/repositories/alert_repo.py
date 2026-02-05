# why: 모듈 역할과 책임을 명확히 하기 위한 진입 주석
from sqlalchemy.orm import Session
from app.core.crypto import encrypt_value
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertRepository:
    """알림 규칙 데이터 접근 계층."""

    def list_alerts(self, db: Session) -> list[Alert]:
        return db.query(Alert).order_by(Alert.created_at.desc()).all()

    def get_alert(self, db: Session, alert_id: int) -> Alert | None:
        return db.query(Alert).filter(Alert.id == alert_id).first()

    def create_alert(self, db: Session, payload: AlertCreate) -> Alert:
        data = payload.model_dump()
        data["destination_value"] = encrypt_value(data["destination_value"])
        alert = Alert(**data)
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def update_alert(self, db: Session, alert: Alert, payload: AlertUpdate) -> Alert:
        update_data = payload.model_dump(exclude_unset=True)
        if "destination_value" in update_data and update_data["destination_value"] is not None:
            update_data["destination_value"] = encrypt_value(update_data["destination_value"])
        for key, value in update_data.items():
            setattr(alert, key, value)
        db.commit()
        db.refresh(alert)
        return alert

    def delete_alert(self, db: Session, alert: Alert) -> None:
        db.delete(alert)
        db.commit()
