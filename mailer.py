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
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    sender = os.environ.get("EMAIL_FROM", user or "")
    recipients = os.environ.get("EMAIL_TO", "")

    if not (host and user and password and recipients):
        log.warning("SMTP-breytur vantar — sleppi pósti. "
                    "(Settu SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_TO.)")
        return False

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
