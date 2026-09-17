import smtplib
from email.message import EmailMessage
from importlib.resources import files

from morning_digest.domain import DeliveryResult, Digest


class GmailDelivery:
    def __init__(self, username: str, app_password: str, recipient: str, sender_name: str = "Morning Digest") -> None:
        self.username, self.app_password, self.recipient, self.sender_name = username, app_password, recipient, sender_name

    def send(self, digest: Digest, subject_prefix: str = "Morning Digest") -> DeliveryResult:
        message = self._build_message(digest, subject_prefix)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
                smtp.login(self.username, self.app_password)
                response = smtp.send_message(message)
            return DeliveryResult(status="success", provider_message_id="accepted" if not response else str(response))
        except Exception as exc:
            return DeliveryResult(status="failed", error=str(exc))

    def _build_message(self, digest: Digest, subject_prefix: str) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = f"{subject_prefix} — {digest.execution_date}"
        message["From"] = f"{self.sender_name} <{self.username}>"
        message["To"] = self.recipient
        message.set_content("HTML対応メールクライアントでご覧ください。")
        message.add_alternative(digest.html_content, subtype="html")
        if "cid:morning-digest-coffee" in digest.html_content:
            image = files("morning_digest").joinpath("assets/coffee-cup.jpg").read_bytes()
            message.get_payload()[-1].add_related(
                image, maintype="image", subtype="jpeg",
                cid="<morning-digest-coffee>", filename="coffee-cup.jpg")
        return message
