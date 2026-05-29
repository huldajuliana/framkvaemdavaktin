# -*- coding: utf-8 -*-
"""
mailer.py — sendir daglega póstinn um SMTP.
Öll leyniorð koma úr umhverfisbreytum (GitHub Secrets) — ALDREI í kóðanum.
Ef SMTP-breyturnar vantar er einfaldlega sleppt að senda (vefurinn keyrir samt).
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("mailer")


def send(subject: str, html_body: str) -> bool:
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASS", "").strip()
    sender = os.environ.get("EMAIL_FROM", "").strip() or user
    recipients = os.environ.get("EMAIL_TO", "").strip()

    # Engar SMTP-stillingar (eða þær tómar) -> sleppum pósti, vefurinn keyrir samt.
    if not (host and user and password and recipients):
        log.warning("SMTP-breytur vantar — sleppi pósti. "
                    "(Settu SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_TO.)")
        return False

    port_raw = os.environ.get("SMTP_PORT", "").strip()
    port = int(port_raw) if port_raw.isdigit() else 587

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipients
    msg.attach(MIMEText("Skoðaðu HTML-útgáfuna af þessum pósti.", "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [r.strip() for r in recipients.split(",")],
                            msg.as_string())
        log.info("Póstur sendur til %s", recipients)
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("Póstsending mistókst: %s", exc)
        return False
