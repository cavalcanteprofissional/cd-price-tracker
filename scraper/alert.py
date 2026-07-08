import os

import resend

resend.api_key = os.environ.get("RESEND_API_KEY", "")


def send_alert(message: str) -> None:
    resend.Emails.send(
        {
            "from": os.environ.get("RESEND_FROM_EMAIL", ""),
            "to": os.environ.get("ALERT_EMAIL", ""),
            "subject": "[CD PRICE TRACKER] Falha no pipeline semanal",
            "text": message,
        }
    )
