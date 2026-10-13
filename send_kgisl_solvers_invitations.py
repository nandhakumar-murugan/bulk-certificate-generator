import os
import sys
import time
import json
import csv
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd

TEMPLATE_PATH = Path(r"c:\Users\smnk2\Downloads\certificate generater\kgisl_solvers_invitation_email_template.html")
STUDENTS_CSV = Path(r"C:\Users\smnk2\Downloads\master_student_personal_emails.csv")
LOG_CSV = Path(r"C:\Users\smnk2\Downloads\kgisl_solvers_dispatch_log.csv")
LOG_JSON = Path(r"C:\Users\smnk2\Downloads\kgisl_solvers_dispatch_log.json")

SENDER_EMAIL = "smnk2006@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def dispatch_invitations(app_password: str):
    if not STUDENTS_CSV.exists():
        print(f"Error: Students CSV not found at {STUDENTS_CSV}")
        return False
    if not TEMPLATE_PATH.exists():
        print(f"Error: Template not found at {TEMPLATE_PATH}")
        return False

    df = pd.read_csv(STUDENTS_CSV)
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        base_html = f.read()

    print(f"Loaded {len(df)} personal student emails from {STUDENTS_CSV.name}")
    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT} via SSL for {SENDER_EMAIL}...")

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, app_password)
        print("Authenticated successfully with Google SMTP!\n")
    except Exception as e:
        print(f"SMTP Authentication Failed: {e}", file=sys.stderr)
        return False

    dispatch_records = []
    success_count = 0
    fail_count = 0

    print("=" * 65)
    print("STARTING KGISL-CAMPUS-SOLVERS PERSONAL EMAIL DISPATCH")
    print("=" * 65)

    for idx, row in df.iterrows():
        student_name = str(row.get("Student Name", "")).strip()
        to_email = str(row.get("Personal Email", "")).strip().lower()
        dept = str(row.get("Department / Detail", "")).strip()
        
        display_name = student_name if student_name and student_name != "nan" else "Fellow Developer"
        subject = f"🚀 {display_name}, build with Gemini 3.8 Flash on KGISL-CAMPUS-SOLVERS!"
        
        html_body = base_html.replace("{{STUDENT_NAME}}", display_name)

        msg = MIMEMultipart("alternative")
        msg["From"] = f"Google Student Ambassador Community <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        status = "Pending"
        sent_timestamp = ""

        try:
            print(f"[{idx+1:02d}/{len(df)}] Sending to {display_name} <{to_email}>...")
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            status = "Delivered"
            sent_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            success_count += 1
            print(f"  -> Delivered successfully! ({sent_timestamp})")
            time.sleep(1.2)  # Respect rate limit
        except Exception as e:
            status = f"Failed: {e}"
            fail_count += 1
            print(f"  -> Failed to send to {to_email}: {e}")

        dispatch_records.append({
            "Serial_No": idx + 1,
            "Student_Name": display_name,
            "Personal_Email": to_email,
            "Department": dept,
            "Delivery_Status": status,
            "Sent_Timestamp": sent_timestamp
        })

    server.quit()

    # Save CSV Audit Log
    with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Serial_No", "Student_Name", "Personal_Email", "Department", "Delivery_Status", "Sent_Timestamp"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dispatch_records)

    # Save JSON Audit Log
    with open(LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(dispatch_records, f, indent=2)

    print("\n" + "=" * 65)
    print(f"DISPATCH COMPLETE! Sent: {success_count}/{len(df)} | Failed: {fail_count}")
    print(f"CSV Audit Log:  {LOG_CSV}")
    print(f"JSON Audit Log: {LOG_JSON}")
    print("=" * 65)
    return True

if __name__ == "__main__":
    pw = "hocnlwthvfmbxpcq"
    if len(sys.argv) > 1:
        pw = sys.argv[1].strip()
    dispatch_invitations(pw)
