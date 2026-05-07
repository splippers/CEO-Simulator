"""
Send a test email to a staff role in the CEO-Simulator mailserver.
Usage: python3 harness/test_mail.py [role] [subject]
   If no args, sends a default test to ceo@.
   Reads body from stdin if piped, otherwise uses a canned message.
"""

from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage

HOST = os.environ.get("MAIL_HOST", "127.0.0.1")
PORT = int(os.environ.get("MAIL_PORT", "25"))
DOMAIN = os.environ.get("DOMAIN", "biab.local")
ROLE = sys.argv[1] if len(sys.argv) > 1 else "ceo"
SUBJECT = sys.argv[2] if len(sys.argv) > 2 else f"Test email for {ROLE} from the board"

if not sys.stdin.isatty():
    BODY = sys.stdin.read()
else:
    BODY = f"""Hi {ROLE.capitalize()},

This is a test message from the CEO-Simulator test harness.

Please review the attached proposal and let me know your thoughts.

Best,
The Board"""


def main() -> None:
    msg = EmailMessage()
    msg["To"] = f"{ROLE}@{DOMAIN}"
    msg["From"] = f"board@{DOMAIN}"
    msg["Subject"] = SUBJECT
    msg.set_content(BODY)

    print(f"Sending to {ROLE}@{DOMAIN} via {HOST}:{PORT}")
    print(f"Subject: {SUBJECT}")
    print()

    with smtplib.SMTP(HOST, PORT, timeout=10) as s:
        s.send_message(msg)

    print("OK - email sent")
    print()
    print(f"Check: curl http://localhost:{os.environ.get('CEO_CENTRAL_PORT', '8080')}/api/jobs")


if __name__ == "__main__":
    main()
