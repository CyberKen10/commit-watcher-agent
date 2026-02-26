#!/usr/bin/env python3
"""Optional helper to send test emails using Gmail SMTP env vars."""

import os
import sys
import smtplib
from email.message import EmailMessage

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587
DEFAULT_GMAIL_SENDER = "kendryjavierdelpino@gmail.com"

EMAIL_USER = os.environ.get("EMAIL_USERNAME", DEFAULT_GMAIL_SENDER)
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO_LIST", DEFAULT_GMAIL_SENDER)


def send_email(subject: str, body: str) -> None:
    if not EMAIL_PASS:
        raise RuntimeError(
            "EMAIL_PASSWORD es obligatorio. En Gmail debes usar un App Password (16 caracteres), no tu contraseña normal."
        )

    message = EmailMessage()
    message["From"] = EMAIL_USER
    message["To"] = EMAIL_TO
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(message)


if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "Test Commit Watcher"
    body = sys.argv[2] if len(sys.argv) > 2 else "Correo de prueba desde commit watcher agent."
    send_email(subject, body)
    print("Correo enviado.")
