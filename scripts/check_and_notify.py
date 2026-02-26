#!/usr/bin/env python3
"""Monitor a public GitHub repository and send commit summaries by email."""

import os
import re
import html
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
    return "\n".join(diff_parts), data.get("commit", {}).get("message", ""), files


def build_before_after_section(files, max_lines_per_side=8):
    """Build a readable before/after view from git patch hunks."""
    if not files:
        return "(No se encontraron archivos modificados en el commit.)"

    sections = []
    for changed_file in files:
        filename = changed_file.get("filename", "(archivo sin nombre)")
        status = changed_file.get("status", "modified")
        patch = changed_file.get("patch", "")

        removed_lines = []
        added_lines = []

        for line in patch.splitlines():
            if line.startswith("---") or line.startswith("+++"):
                continue
            if line.startswith("-"):
                removed_lines.append(line[1:])
            elif line.startswith("+"):
                added_lines.append(line[1:])

        removed_preview = removed_lines[:max_lines_per_side]
        added_preview = added_lines[:max_lines_per_side]

        removed_text = "\n".join(f"- {item}" for item in removed_preview) or "- (sin líneas removidas)"
        added_text = "\n".join(f"+ {item}" for item in added_preview) or "+ (sin líneas agregadas)"

        removed_note = ""
        added_note = ""
        if len(removed_lines) > max_lines_per_side:
            removed_note = f"\n- ... ({len(removed_lines) - max_lines_per_side} líneas removidas adicionales)"
        if len(added_lines) > max_lines_per_side:
            added_note = f"\n+ ... ({len(added_lines) - max_lines_per_side} líneas agregadas adicionales)"

        sections.append(
            (
                f"Archivo: {filename} (status: {status})\n"
                "Antes del commit (líneas removidas):\n"
                f"{removed_text}{removed_note}\n\n"
                "Después del commit (líneas agregadas):\n"
                f"{added_text}{added_note}\n"
            )
        )

    return "\n\n".join(sections)


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
7) Para cada archivo, explica explícitamente: qué había antes, qué hay ahora y la comparación funcional entre ambos estados.

Importante:
- Argumenta más las explicaciones técnicas: no sólo digas qué cambió, explica por qué podría haberse hecho y qué efecto produce en el comportamiento.
- Si faltan líneas de contexto, indica supuestos razonables.

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



def _linkify_issue_references(text):
    """Convert issue references and URLs in plain text into HTML links."""
    issue_pattern = re.compile(r"(?<![\w/])#(\d+)")
    url_pattern = re.compile(r"(https?://[^\s<>()]+)")

    escaped = html.escape(text)

    def issue_replacer(match):
        issue_number = match.group(1)
        issue_url = f"https://github.com/{OWNER}/{REPO}/issues/{issue_number}"
        return f'<a href="{issue_url}">#{issue_number}</a>'

    def url_replacer(match):
        url = match.group(1)
        return f'<a href="{url}">{url}</a>'

    linked_urls = url_pattern.sub(url_replacer, escaped)
    return issue_pattern.sub(issue_replacer, linked_urls)


def build_html_email_body(body_text):
    """Return HTML representation so links are clickable in email clients."""
    linked_content = _linkify_issue_references(body_text)
    return f"""
<html>
  <body>
    <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{linked_content}</pre>
  </body>
</html>
"""


def send_email(subject, body_text, body_html=None):
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
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

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
    diff_text, commit_message, files = get_commit_diff(sha)
    if not diff_text:
        diff_text = "(no hay patch disponible; tal vez sólo cambios binarios o merge)"

    before_after_section = build_before_after_section(files)

    print("Generando resumen con OpenAI...")
    summary = summarize_with_openai(diff_text, commit_message)

    subject = f"[Commit Watch] {OWNER}/{REPO} {sha[:7]}"
    body_text = (
        f"Repo: {OWNER}/{REPO}\n"
        f"Commit: {sha}\n"
        f"Message: {commit_message}\n\n"
        "Cambios por archivo (antes vs después):\n"
        f"{before_after_section}\n\n"
        f"Resumen:\n{summary}"
    )

    body_html = build_html_email_body(body_text)

    print("Enviando email...")
    send_email(subject, body_text, body_html=body_html)

    # guardar SHA para no procesarlo otra vez
    write_last_sha(sha)
    print("Listo. SHA guardado:", sha)


if __name__ == "__main__":
    main()
