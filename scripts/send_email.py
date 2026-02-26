#!/usr/bin/env python3
"""Optional helper to send test emails using the same SMTP env vars."""

import os
import sys
import smtplib
from email.message import EmailMessage

EMAIL_USER = os.environ.get("EMAIL_USERNAME")
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO_LIST", "tu@correo.com")


def send_email(subject: str, body: str) -> None:
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError("EMAIL_USERNAME y EMAIL_PASSWORD son obligatorios.")

    message = EmailMessage()
    message["From"] = EMAIL_USER
    message["To"] = EMAIL_TO
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(message)


if __name__ == "__main__":
    subject = sys.argv[1] if len(sys.argv) > 1 else "Test Commit Watcher"
    body = sys.argv[2] if len(sys.argv) > 2 else "Correo de prueba desde commit watcher agent."
    send_email(subject, body)
    print("Correo enviado.")
