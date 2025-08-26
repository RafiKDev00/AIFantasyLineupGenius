#"B''SD"
# notifier.py

import os, smtplib, ssl

'''
    We use "Simple Mail Transfer Protocol" (had to look up what it stands for tbh),
    we send via server 587 (most modern and still secure)
    we send via email(e.g., Gmail with an App Password).
    AND if any SMTP env is missing, we just log and skip sending (no crash) - really for debuggin BEZH shouldn't come to this.
'''

def notify_via_email(subject: str, body: str):
    host = os.getenv("SMTP_HOST")               # e.g., smtp.gmail.com
    port = int(os.getenv("SMTP_PORT", "587"))   # 587 for STARTTLS
    user = os.getenv("SMTP_USER")               # from address / login
    pwd  = os.getenv("SMTP_PASS")               # app password / SMTP key
    to   = os.getenv("ALERT_TO", user)          # default to self
    

    if not all([host, port, user, pwd, to]):
        print("Email failed to send (missing SMTP_* env). Subject:", subject)
        return

    msg = f"From: {user}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as s:
        s.starttls(context=ctx)   #encrypts/secures connection
        s.login(user, pwd)   # authenticates email and password - a legality check to see if I really have access to this
        s.sendmail(user, [to], msg)             # send it
