import os
import sys
import time
import json
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

BASE_DIR = Path(r"c:\Users\smnk2\Downloads\certificate generater")
TEMPLATE_PATH = BASE_DIR / "product_understanding_email_template.html"
CERTS_DIR = BASE_DIR / "generated_certificates" / "product_understanding"
REGISTRY_JSON = CERTS_DIR / "registry_product_understanding.json"

SENDER_EMAIL = "smnk2006@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def send_all(app_password: str):
    if not os.path.exists(REGISTRY_JSON):
        print(f"Error: Registry not found at {REGISTRY_JSON}")
        return False
        
    with open(REGISTRY_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)
        
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        base_html = f.read()

    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT} via SSL for {SENDER_EMAIL}...")
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, app_password)
        print("Authenticated successfully with Google SMTP!\n")
    except Exception as e:
        print(f"SMTP Authentication Failed: {e}", file=sys.stderr)
        print("\nPlease ensure you are using a 16-character Google App Password (not your normal Google account password).")
        print("Generate one at: https://myaccount.google.com/apppasswords")
        return False

    success_count = 0
    fail_count = 0

    for idx, rec in enumerate(records, 1):
        name = rec["name"]
        to_email = rec["email"]
        cert_id = rec["cert_id"]
        pdf_path = CERTS_DIR / rec["pdf_file"]
        png_path = CERTS_DIR / rec["png_file"]
        
        subject = f"🎉 Congratulations {name}! Your Official Google Certificate of Participation is Here"
        
        html_body = base_html.replace("{{STUDENT_NAME}}", name)
        html_body = html_body.replace("{{CERTIFICATE_ID}}", cert_id)
        
        msg = MIMEMultipart()
        msg["From"] = f"Google Student Ambassador Community <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        # Attach PDF
        if pdf_path.exists():
            with open(pdf_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=pdf_path.name)
            part["Content-Disposition"] = f'attachment; filename="{pdf_path.name}"'
            msg.attach(part)
            
        # Attach PNG
        if png_path.exists():
            with open(png_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=png_path.name)
            part["Content-Disposition"] = f'attachment; filename="{png_path.name}"'
            msg.attach(part)
            
        try:
            print(f"[{idx}/{len(records)}] Sending to {name} <{to_email}>...")
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            print(f"  -> Delivered successfully! (ID: {cert_id})")
            rec["delivery_status"] = "Delivered"
            rec["sent_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            success_count += 1
            time.sleep(1.5)  # Respect delivery rate limit
        except Exception as e:
            print(f"  -> Failed to send to {to_email}: {e}")
            rec["delivery_status"] = f"Failed: {e}"
            fail_count += 1

    server.quit()

    # Save updated registry
    with open(REGISTRY_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    
    # Also update CSV
    import csv
    csv_path = CERTS_DIR / "registry_product_understanding.csv"
    if records:
        fieldnames = list(records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    print(f"\n==========================================")
    print(f"Dispatch Complete! Sent: {success_count}/{len(records)} | Failed: {fail_count}")
    print(f"Registry updated: {REGISTRY_JSON}")
    print(f"==========================================")
    return True

if __name__ == "__main__":
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if len(sys.argv) > 1:
        pw = sys.argv[1].strip()
    elif not pw:
        import getpass
        pw = getpass.getpass("Enter Google App Password (16-char): ").strip()
    
    if pw:
        send_all(pw)
    else:
        print("Password cannot be blank.")
