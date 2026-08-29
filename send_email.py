#!/usr/bin/env python3
"""
Email Dispatcher for Certificate Distribution
Sends personalized certificates as attachments along with the responsive HTML email template.
"""

import os
import sys
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

DEFAULT_TEMPLATE_PATH = "email_template.html"

def send_certificate_email(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    student_name: str,
    attachment_paths: list,
    subject: str = "🎉 Congratulations! Your Official Certificate of Participation is Here | Fund My Crazy Build Night with Gemini",
    template_path: str = DEFAULT_TEMPLATE_PATH,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 465
) -> bool:
    """
    Sends an HTML email with attached certificate files using SMTP SSL.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Email template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Replace dynamic placeholders
    html_content = html_content.replace("{{STUDENT_NAME}}", student_name)
    html_content = html_content.replace("[Participant Name]", student_name)

    # Create MIMEMultipart message
    msg = MIMEMultipart()
    msg["From"] = f"Google Student Ambassador Community <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Attach HTML body
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Attach certificate files
    for file_path in attachment_paths:
        path = Path(file_path)
        if path.exists():
            with open(path, "rb") as f:
                part = MIMEApplication(f.read(), Name=path.name)
            part["Content-Disposition"] = f'attachment; filename="{path.name}"'
            msg.attach(part)
            print(f"  -> Attached: {path.name}")
        else:
            print(f"  -> Warning: Attachment not found: {file_path}")

    # Send via SMTP SSL
    print(f"Connecting to {smtp_server}:{smtp_port}...")
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

    print(f"Successfully sent email to {recipient_email}!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Send certificate distribution email.")
    parser.add_argument("--to", default="smnk2006@gmail.com", help="Recipient email address.")
    parser.add_argument("--name", default="Nandhakumar M", help="Recipient student name.")
    parser.add_argument("--from-email", default="smnk2006@gmail.com", help="Sender Gmail address.")
    parser.add_argument("--password", default=None, help="Google App Password (16 characters).")
    parser.add_argument("--attachment", nargs="*", default=None, help="Paths to attachments.")
    
    args = parser.parse_args()

    sender_email = args.from_email
    recipient_email = args.to
    student_name = args.name

    # Check password from arg, env var, or prompt
    password = args.password or os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        print("\n=======================================================")
        print("🔑 Google App Password Required")
        print("=======================================================")
        print("To send emails via Gmail SMTP, Google requires a 16-character App Password.")
        print("You can generate one in 30 seconds at: https://myaccount.google.com/apppasswords")
        print("=======================================================\n")
        import getpass
        password = getpass.getpass("Enter your 16-character Google App Password: ").strip()

    if not password:
        print("Error: Password cannot be blank.", file=sys.stderr)
        sys.exit(1)

    attachments = args.attachment or [
        "sample_mail_assets/Nandhakumar_M_Certificate.pdf",
        "sample_mail_assets/Nandhakumar_M_Certificate.png"
    ]

    try:
        send_certificate_email(
            sender_email=sender_email,
            sender_password=password,
            recipient_email=recipient_email,
            student_name=student_name,
            attachment_paths=attachments
        )
    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication Error: Gmail rejected the login.", file=sys.stderr)
        print("Make sure you are using a 16-character Google App Password (not your normal Gmail password).", file=sys.stderr)
        print("Generate one here: https://myaccount.google.com/apppasswords", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error sending email: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

