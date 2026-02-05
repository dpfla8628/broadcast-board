# why: 이메일 알림 발송을 위한 최소 SMTP 클라이언트
import smtplib
from email.message import EmailMessage

from common.config import get_batch_settings


def send_email_message(to_address: str, subject: str, body: str) -> None:
    """SMTP로 이메일 발송.

    - why: MVP에서 외부 이메일 서비스에 의존하지 않고도 동작하도록 기본 SMTP 지원
    """

    settings = get_batch_settings()

    if not settings.smtp_host:
        raise ValueError("SMTP_HOST가 설정되지 않았습니다.")
    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("SMTP_USER / SMTP_PASSWORD가 설정되지 않았습니다.")

    from_email = settings.smtp_from_email or settings.smtp_user

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{from_email}>"
    message["To"] = to_address
    message.set_content(body)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
