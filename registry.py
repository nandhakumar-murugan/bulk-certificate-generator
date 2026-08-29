"""
Certificate Registry & Audit Log Manager
Maintains a persistent ledger of all issued certificates, verification IDs, recipient emails, and delivery statuses.
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

REGISTRY_DIR = "records"
REGISTRY_CSV = os.path.join(REGISTRY_DIR, "certificates_registry.csv")
REGISTRY_JSON = os.path.join(REGISTRY_DIR, "certificates_registry.json")

COLUMNS = [
    "Certificate_ID",
    "Student_Name",
    "Year",
    "Department",
    "Email",
    "Issued_Timestamp",
    "Delivery_Status",
    "PDF_File",
    "PNG_File"
]

def init_registry():
    """Ensures records directory and ledger exist."""
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_CSV):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(REGISTRY_CSV, index=False)

def log_certificate_record(
    cert_id: str,
    name: str,
    year: str,
    department: str,
    email: str = "",
    delivery_status: str = "Generated",
    pdf_path: str = "",
    png_path: str = ""
) -> Dict:
    """Logs or updates an issued certificate record in CSV and JSON ledgers."""
    init_registry()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = {
        "Certificate_ID": str(cert_id).strip(),
        "Student_Name": str(name).strip(),
        "Year": str(year).strip(),
        "Department": str(department).strip(),
        "Email": str(email).strip(),
        "Issued_Timestamp": timestamp,
        "Delivery_Status": str(delivery_status).strip(),
        "PDF_File": str(pdf_path).strip(),
        "PNG_File": str(png_path).strip()
    }

    try:
        df = pd.read_csv(REGISTRY_CSV)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)

    # If Certificate_ID already exists, update it; otherwise append
    if "Certificate_ID" in df.columns and cert_id in df["Certificate_ID"].values:
        idx = df[df["Certificate_ID"] == cert_id].index[0]
        for k, v in record.items():
            df.at[idx, k] = v
    else:
        df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)

    df.to_csv(REGISTRY_CSV, index=False)

    # Also save structured JSON for easy web API access
    try:
        records_list = df.to_dict(orient="records")
        with open(REGISTRY_JSON, "w", encoding="utf-8") as f:
            json.dump(records_list, f, indent=2)
    except Exception as e:
        print(f"Warning: JSON ledger update: {e}")

    return record

def get_registry_dataframe() -> pd.DataFrame:
    """Returns the full certificate registry as a pandas DataFrame."""
    init_registry()
    if os.path.exists(REGISTRY_CSV):
        try:
            return pd.read_csv(REGISTRY_CSV)
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def get_record_by_id(cert_id: str) -> Optional[Dict]:
    """Look up a certificate by ID."""
    df = get_registry_dataframe()
    if not df.empty and "Certificate_ID" in df.columns:
        match = df[df["Certificate_ID"].astype(str).str.upper() == str(cert_id).strip().upper()]
        if not match.empty:
            return match.iloc[0].to_dict()
    return None
