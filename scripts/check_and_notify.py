#!/usr/bin/env python3
"""Monitor a public GitHub repository and send commit summaries by email."""

import os
import requests
import smtplib
from email.message import EmailMessage

OWNER = os.environ.get("TARGET_OWNER")  # dueño del repo público
REPO = os.environ.get("TARGET_REPO")  # nombre repo público
GITHUB_TOKEN = os.environ.get("GH_TOKEN_CUSTOM") or os.environ.get("GITHUB_TOKEN_CUSTOM")
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587
DEFAULT_GMAIL_SENDER = "kendryjavierdelpino@gmail.com"

EMAIL_USER = os.environ.get("EMAIL_USERNAME", DEFAULT_GMAIL_SENDER)
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO_LIST", DEFAULT_GMAIL_SENDER)  # comma separated

GITHUB_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def get_latest_commit():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    print("TOKEN:", os.environ.get("GITHUB_TOKEN_CUSTOM"))
    print("GH_TOKEN_CUSTOM:", os.environ.get("GH_TOKEN_CUSTOM"))
    response = requests.get(url, headers=GITHUB_HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()[0]  # última entrada


def get_commit_diff(sha):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{sha}"
    print("TOKEN:", os.environ.get("GITHUB_TOKEN_CUSTOM"))
    print("GH_TOKEN_CUSTOM:", os.environ.get("GH_TOKEN_CUSTOM"))
    response = requests.get(url, headers=GITHUB_HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    files = data.get("files", [])
    diff_parts = []
    for changed_file in files:
        if "patch" in changed_file:
            diff_parts.append(f"File: {changed_file['filename']}\n{changed_file['patch']}\n")
    return "\n".join(diff_parts), data.get("commit", {}).get("message", "")


def read_last_sha(path="last_sha.txt"):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return ""


def write_last_sha(sha, path="last_sha.txt"):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(sha)


def summarize_with_openai(diff_text, commit_message):
    system = (
        "Eres un ingeniero senior especializado en revisión de código. "
        "Responde de forma técnica y concisa."
    )
    user_prompt = f"""Analiza el siguiente commit/diff y genera un informe con:
1) Archivos modificados
2) Tipo de cambio (feature/fix/refactor/docs/test/breaking)
3) Resumen técnico de los cambios
4) Motivo probable del cambio (basado en diff y commit message)
5) Impacto técnico
6) Riesgos y recomendaciones

Commit message:
{commit_message}

Diff:
{diff_text}
"""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",  # puedes cambiar a otro modelo disponible
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 800,
        "temperature": 0.2,
    }
    print("OPENAI_API_KEY presente:", bool(os.environ.get("OPENAI_API_KEY")))
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def send_email(subject, body):
    print("EMAIL_USERNAME presente:", bool(os.environ.get("EMAIL_USERNAME")))
    print("EMAIL_PASSWORD presente:", bool(os.environ.get("EMAIL_PASSWORD")))
    print("EMAIL_TO_LIST presente:", bool(os.environ.get("EMAIL_TO_LIST")))

    if not EMAIL_PASS:
        print(
            "EMAIL_PASSWORD no está configurado. Para Gmail usa un App Password (16 caracteres) y exporta EMAIL_PASSWORD."
        )
        print("Saltando envío de email.")
        return

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


def main():
    print("TARGET_OWNER:", OWNER)
    print("TARGET_REPO:", REPO)
    print("GH_TOKEN_CUSTOM presente:", bool(os.environ.get("GH_TOKEN_CUSTOM")))
    print("GITHUB_TOKEN_CUSTOM presente (legacy):", bool(os.environ.get("GITHUB_TOKEN_CUSTOM")))

    if not OWNER or not REPO:
        raise ValueError("TARGET_OWNER y TARGET_REPO deben estar definidos.")
    if not GITHUB_TOKEN:
        raise ValueError("GH_TOKEN_CUSTOM (o legado GITHUB_TOKEN_CUSTOM) debe estar definido.")

    latest = get_latest_commit()
    sha = latest["sha"]
    commit_message = latest["commit"]["message"]
    last_sha = read_last_sha()

    if sha == last_sha:
        print("No hay commits nuevos. SHA igual:", sha)
        return

    print("Nuevo commit detectado:", sha)
    diff_text, commit_message = get_commit_diff(sha)
    if not diff_text:
        diff_text = "(no hay patch disponible; tal vez sólo cambios binarios o merge)"

    print("Generando resumen con OpenAI...")
    summary = summarize_with_openai(diff_text, commit_message)

    subject = f"[Commit Watch] {OWNER}/{REPO} {sha[:7]}"
    body = (
        f"Repo: {OWNER}/{REPO}\n"
        f"Commit: {sha}\n"
        f"Message: {commit_message}\n\n"
        f"Resumen:\n{summary}"
    )

    print("Enviando email...")
    send_email(subject, body)

    # guardar SHA para no procesarlo otra vez
    write_last_sha(sha)
    print("Listo. SHA guardado:", sha)


if __name__ == "__main__":
    main()
