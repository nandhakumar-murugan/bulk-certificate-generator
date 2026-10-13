import os
import json
import fitz
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(r"c:\Users\smnk2\Downloads\certificate generater")
OUT_DIR = BASE_DIR / "generated_certificates" / "product_understanding"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AI_TEMPLATE = str(BASE_DIR / "google_cert_master.ai")
FONT_BOLD = str(BASE_DIR / "assets" / "fonts" / "GoogleSans-Bold.ttf")
FONT_MED = str(BASE_DIR / "assets" / "fonts" / "GoogleSans-Medium.ttf")
SIG_PATH = r"C:\Users\smnk2\Downloads\SIGNATURE_100KB-removebg-preview.png"

# Verified Submissions for Product Understanding Challenge (5 September 2026)
STUDENTS = [
    {"name": "JANAKARAJ T", "email": "janakarajthangaraj1973@gmail.com", "cert_id": "GSA-PU-2026-001"},
    {"name": "Micheal Anand A", "email": "michealanand124123@gmail.com", "cert_id": "GSA-PU-2026-002"},
    {"name": "SATHISHKUMAR K H", "email": "sathish123bk@gmail.com", "cert_id": "GSA-PU-2026-003"},
    {"name": "PRABAKAR A", "email": "prabakar2699@gmail.com", "cert_id": "GSA-PU-2026-004"},
    {"name": "RAM ABISHEIK R", "email": "ramabisheikr@gmail.com", "cert_id": "GSA-PU-2026-005"},
    {"name": "ABDUL RAFI N", "email": "abdulrafi.n2007@gmail.com", "cert_id": "GSA-PU-2026-006"},
    {"name": "Jamal Arsh M", "email": "djnobita001@gmail.com", "cert_id": "GSA-PU-2026-007"},
]

def generate_all():
    records = []
    print(f"Generating {len(STUDENTS)} certificates using Google Official Master Template...")
    
    for idx, s in enumerate(STUDENTS, 1):
        doc = fitz.open(AI_TEMPLATE)
        page = doc[0]
        
        # Register Fonts
        page.insert_font(fontname="GSBold", fontfile=FONT_BOLD)
        page.insert_font(fontname="GSMed", fontfile=FONT_MED)
        
        # 1. Participant Name (Clean Google Sans Bold, centered above top underline)
        name_rect = fitz.Rect(200, 222, 686, 268)
        page.insert_textbox(name_rect, s["name"], fontname="GSBold", fontsize=24, color=(0.08, 0.08, 0.08), align=fitz.TEXT_ALIGN_CENTER)
        
        # 2. Initiative Name in narrative body
        init_rect = fitz.Rect(250, 320, 650, 352)
        page.insert_textbox(init_rect, "Product Understanding", fontname="GSBold", fontsize=14, color=(0.1, 0.1, 0.1), align=fitz.TEXT_ALIGN_CENTER)
        
        # 3. Institution Name in narrative body
        inst_rect = fitz.Rect(450, 368, 792, 390)
        page.insert_textbox(inst_rect, "KGiSL Institute of Technology", fontname="GSBold", fontsize=13.5, color=(0.1, 0.1, 0.1), align=fitz.TEXT_ALIGN_CENTER)
        
        # 4. Date (5 September, 2026)
        date_rect = fitz.Rect(115, 520, 292, 542)
        page.insert_textbox(date_rect, "5 September, 2026", fontname="GSBold", fontsize=13.5, color=(0.1, 0.1, 0.1), align=fitz.TEXT_ALIGN_CENTER)
        
        # 5. Initiative Name bottom field
        init_btm_rect = fitz.Rect(355, 520, 532, 542)
        page.insert_textbox(init_btm_rect, "Product Understanding", fontname="GSBold", fontsize=13.5, color=(0.1, 0.1, 0.1), align=fitz.TEXT_ALIGN_CENTER)
        
        # 6. Nandhakumar's Real Signature Image
        sig_rect = fitz.Rect(630, 480, 735, 540)
        page.insert_image(sig_rect, filename=SIG_PATH)
        
        # 7. Ambassador Name, GID, and Title under Authorized Signature
        amb_rect = fitz.Rect(596, 575, 770, 605)
        page.insert_textbox(amb_rect, "Nandhakumar M (GID: 36)\nGoogle Student Ambassador", fontname="GSMed", fontsize=8.5, color=(0.3, 0.3, 0.3), align=fitz.TEXT_ALIGN_CENTER)
        
        # 8. Verifiable Certificate ID at bottom margin
        cid_rect = fitz.Rect(300, 612, 586, 628)
        page.insert_textbox(cid_rect, f"Certificate ID: {s['cert_id']}", fontname="GSMed", fontsize=7.5, color=(0.45, 0.45, 0.45), align=fitz.TEXT_ALIGN_CENTER)
        
        # File paths
        clean_name = s["name"].replace(" ", "_").replace(".", "")
        pdf_name = f"{idx:02d}_{clean_name}_{s['cert_id']}.pdf"
        png_name = f"{idx:02d}_{clean_name}_{s['cert_id']}.png"
        
        pdf_path = OUT_DIR / pdf_name
        png_path = OUT_DIR / png_name
        
        # Save authentic Vector PDF
        doc.save(str(pdf_path))
        
        # Save 300 DPI high-resolution PNG (3692 x 2658 px)
        pix = page.get_pixmap(dpi=300)
        pix.save(str(png_path))
        
        records.append({
            "serial_no": idx,
            "name": s["name"],
            "email": s["email"],
            "cert_id": s["cert_id"],
            "initiative": "Product Understanding",
            "date": "5 September, 2026",
            "institution": "KGiSL Institute of Technology",
            "ambassador": "Nandhakumar M (GID: 36)",
            "pdf_file": pdf_name,
            "png_file": png_name,
        })
        print(f"[{idx}/{len(STUDENTS)}] Created: {pdf_name} & {png_name}")
        doc.close()
        
    # Save Registry
    registry_json = OUT_DIR / "registry_product_understanding.json"
    registry_csv = OUT_DIR / "registry_product_understanding.csv"
    
    with open(registry_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
        
    df = pd.DataFrame(records)
    df.to_csv(registry_csv, index=False)
    print(f"\nRegistry saved to:\n  - {registry_json}\n  - {registry_csv}")

if __name__ == "__main__":
    generate_all()
