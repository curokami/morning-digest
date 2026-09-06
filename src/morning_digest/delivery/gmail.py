import smtplib
from email.message import EmailMessage

from morning_digest.domain import DeliveryResult, Digest


class GmailDelivery:
    def __init__(self, username: str, app_password: str, recipient: str, sender_name: str = "Morning Digest") -> None:
        self.username, self.app_password, self.recipient, self.sender_name = username, app_password, recipient, sender_name

    def send(self, digest: Digest, subject_prefix: str = "Morning Digest") -> DeliveryResult:
        message = EmailMessage()
        message["Subject"] = f"{subject_prefix} — {digest.execution_date}"
        message["From"] = f"{self.sender_name} <{self.username}>"
        message["To"] = self.recipient
        message.set_content("HTML対応メールクライアントでご覧ください。")
        message.add_alternative(digest.html_content, subtype="html")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
                smtp.login(self.username, self.app_password)
                response = smtp.send_message(message)
            return DeliveryResult(status="success", provider_message_id="accepted" if not response else str(response))
        except Exception as exc:
            return DeliveryResult(status="failed", error=str(exc))
