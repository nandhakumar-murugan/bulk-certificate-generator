#!/usr/bin/env python3
"""
Email Dispatcher & Automated Bulk Sender for Certificate Distribution.
Sends personalized certificates as attachments, records audit logs, and handles delivery rates.
"""

import os
import sys
import time
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Dict, Optional

from registry import log_certificate_record, get_registry_dataframe

DEFAULT_TEMPLATE_PATH = "email_template.html"

def send_certificate_email(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    student_name: str,
    attachment_paths: list,
    subject: str = "🎉 Congratulations! Your Official Certificate of Participation is Here | Fund My Crazy Build Night with Gemini",
    template_path: str = DEFAULT_TEMPLATE_PATH,
    cert_id: str = "",
    year: str = "",
    department: str = "",
    form_url: str = "https://docs.google.com/spreadsheets/d/14BUb23tkmZ-sy8toYp_Ao1vJDHq0ViBgRRVU3GK_q4U/edit?gid=1433488250#gid=1433488250",
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 465
) -> bool:
    """
    Sends an HTML email with optional certificate files using SMTP SSL and logs to registry.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Email template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Replace dynamic placeholders
    html_content = html_content.replace("{{STUDENT_NAME}}", student_name)
    html_content = html_content.replace("[Participant Name]", student_name)
    html_content = html_content.replace("{{SUBMISSION_FORM_URL}}", form_url)

    msg = MIMEMultipart()
    msg["From"] = f"Google Student Ambassador Community <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Attach HTML body
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Attach certificate files if provided
    if attachment_paths:
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
        else:
            print(f"  -> Warning: Attachment not found: {file_path}")

    try:
        # Send via SMTP SSL
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print(f"Successfully sent email to {recipient_email}!")
        
        # Log to registry
        log_certificate_record(
            cert_id=cert_id or "GSA-FMC-2026-001",
            name=student_name,
            year=year,
            department=department,
            email=recipient_email,
            delivery_status="Email Delivered",
            pdf_path=str(attachment_paths[0]) if attachment_paths else "",
            png_path=str(attachment_paths[1]) if len(attachment_paths) > 1 else ""
        )
        return True

    except Exception as ex:
        log_certificate_record(
            cert_id=cert_id or "GSA-FMC-2026-001",
            name=student_name,
            year=year,
            department=department,
            email=recipient_email,
            delivery_status=f"Failed: {str(ex)[:50]}",
            pdf_path=str(attachment_paths[0]) if attachment_paths else "",
            png_path=str(attachment_paths[1]) if len(attachment_paths) > 1 else ""
        )
        raise ex

def send_bulk_certificates(
    records: List[Dict[str, str]],
    sender_email: str,
    sender_password: str,
    generator=None,
    output_dir: str = "generated_certificates",
    progress_callback=None,
    delay_seconds: float = 1.2
) -> Dict:
    """
    Automated bulk dispatcher: generates certificate and emails each participant in list.
    """
    if generator is None:
        from certificate_engine import CertificateGenerator
        generator = CertificateGenerator()

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    results = {"total": len(records), "sent": 0, "failed": 0, "errors": []}

    for idx, rec in enumerate(records):
        name = rec.get("name", "").strip()
        email = rec.get("email", "").strip()
        year = rec.get("year", "").strip()
        dept = rec.get("department", "").strip()
        cid = rec.get("cert_id") or f"GSA-FMC-2026-{idx+1:03d}"

        if not email or "@" not in email:
            print(f"Skipping {name} (No valid email: '{email}')")
            continue

        try:
            # 1. Render certificate
            img = generator.render_certificate(name=name, year=year, department=dept, cert_id=cid)
            safe_name = name.replace(" ", "_")
            png_path = out_path / f"{safe_name}.png"
            pdf_path = out_path / f"{safe_name}.pdf"
            img.save(str(png_path))
            generator.generate_single_pdf(img, str(pdf_path))

            # 2. Send email
            send_certificate_email(
                sender_email=sender_email,
                sender_password=sender_password,
                recipient_email=email,
                student_name=name,
                cert_id=cid,
                year=year,
                department=dept,
                attachment_paths=[str(pdf_path), str(png_path)]
            )
            results["sent"] += 1
            time.sleep(delay_seconds)

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"name": name, "email": email, "error": str(e)})
            print(f"Error sending to {email}: {e}")

        if progress_callback:
            progress_callback(idx + 1, len(records))

    return results

def main():
    parser = argparse.ArgumentParser(description="Send certificate distribution email.")
    parser.add_argument("--to", default="smnk2006@gmail.com", help="Recipient email address.")
    parser.add_argument("--name", default="Nandhakumar M", help="Recipient student name.")
    parser.add_argument("--from-email", default="smnk2006@gmail.com", help="Sender Gmail address.")
    parser.add_argument("--password", default=None, help="Google App Password (16 characters).")
    parser.add_argument("--attachment", nargs="*", default=None, help="Paths to attachments.")
    parser.add_argument("--bulk-file", default=None, help="CSV/Excel file for bulk email dispatch.")
    
    args = parser.parse_args()

    sender_email = args.from_email
    password = args.password or os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        import getpass
        password = getpass.getpass("Enter your 16-character Google App Password: ").strip()

    if not password:
        print("Error: Password cannot be blank.", file=sys.stderr)
        sys.exit(1)

    if args.bulk_file:
        from certificate_engine import parse_records_from_file
        records = parse_records_from_file(args.bulk_file)
        print(f"Starting bulk email dispatch for {len(records)} participants...")
        results = send_bulk_certificates(records, sender_email, password)
        print(f"Bulk Dispatch Finished! Sent: {results['sent']}, Failed: {results['failed']}")
    else:
        attachments = args.attachment or [
            "sample_mail_assets/Nandhakumar_M_Certificate.pdf",
            "sample_mail_assets/Nandhakumar_M_Certificate.png"
        ]
        send_certificate_email(
            sender_email=sender_email,
            sender_password=password,
            recipient_email=args.to,
            student_name=args.name,
            cert_id="GSA-FMC-2026-001",
            year="III Year",
            department="Computer Science & Cyber Security",
            attachment_paths=attachments
        )

if __name__ == "__main__":
    main()
