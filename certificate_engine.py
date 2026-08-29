import os
import io
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

DEFAULT_TEMPLATE = "Certificate of Participation - Fund My Crazy Build Night (1).png"
CLEAN_TEMPLATE = "template_cleaned.png"

# Coordinates & Constants for the certificate template (1180 x 850)
UNDERLINE_Y = 460
UNDERLINE_X_START = 321
UNDERLINE_X_END = 858
TEMPLATE_WIDTH = 1180
TEMPLATE_HEIGHT = 850

# Bundled official Google Sans fonts in the repository
ASSETS_FONT_DIR = Path(__file__).parent / "assets" / "fonts"
FONT_GOOGLE_SANS_BOLD = str(ASSETS_FONT_DIR / "GoogleSans-Bold.ttf")
FONT_GOOGLE_SANS_MEDIUM = str(ASSETS_FONT_DIR / "GoogleSans-Medium.ttf")
FONT_GOOGLE_SANS_REGULAR = str(ASSETS_FONT_DIR / "GoogleSans-Regular.ttf")

# Fallback fonts on Windows
SYSTEM_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
]

def get_font_path(prefer_bold: bool = False, weight: str = "auto") -> str:
    """Find the best available font, prioritizing bundled Google Sans for 100% fidelity."""
    # 1. Bundled Google Sans fonts (primary)
    if weight == "bold" or (weight == "auto" and prefer_bold):
        if os.path.exists(FONT_GOOGLE_SANS_BOLD):
            return FONT_GOOGLE_SANS_BOLD
    elif weight == "medium":
        if os.path.exists(FONT_GOOGLE_SANS_MEDIUM):
            return FONT_GOOGLE_SANS_MEDIUM
    elif weight == "regular" or (weight == "auto" and not prefer_bold):
        if os.path.exists(FONT_GOOGLE_SANS_REGULAR):
            return FONT_GOOGLE_SANS_REGULAR

    # Fallback among bundled
    if os.path.exists(FONT_GOOGLE_SANS_BOLD) and prefer_bold:
        return FONT_GOOGLE_SANS_BOLD
    if os.path.exists(FONT_GOOGLE_SANS_REGULAR):
        return FONT_GOOGLE_SANS_REGULAR

    # 2. System fallbacks
    if prefer_bold:
        bolds = [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
        ]
        for p in bolds:
            if os.path.exists(p):
                return p
    for p in SYSTEM_FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return "arial.ttf"

def detect_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Automatically find the Name, Year, Department/Section, optional ID, and Email columns in a dataframe."""
    name_col = None
    year_col = None
    dept_col = None
    id_col = None
    email_col = None
    
    name_keywords = ["name", "participant", "student", "candidate", "full name", "attendee"]
    year_keywords = ["year", "yr", "academic year", "class year", "batch", "sem", "semester"]
    dept_keywords = ["department", "dept", "section", "branch", "stream", "course", "major"]
    id_keywords = ["cert_id", "certificate_id", "id", "serial_no", "serial", "reg_no", "roll_no", "verification_id"]
    email_keywords = ["email", "mail", "email_id", "email id", "email address", "e-mail", "personal_email", "student_email"]

    cols = list(df.columns)
    for c in cols:
        clow = str(c).strip().lower()
        if not email_col and any(k == clow or k in clow for k in email_keywords):
            email_col = c
            continue
        if not id_col and any(k == clow or k in clow for k in id_keywords):
            id_col = c
            continue
        if not name_col and any(k == clow or k in clow for k in name_keywords):
            name_col = c
            continue
        if not year_col and any(k == clow or k in clow for k in year_keywords):
            year_col = c
            continue
        if not dept_col and any(k == clow or k in clow for k in dept_keywords):
            dept_col = c
            continue

    # Fallbacks based on column position if not detected by keywords
    unassigned = [c for c in cols if c not in (name_col, year_col, dept_col, id_col, email_col)]
    if not name_col and unassigned:
        name_col = unassigned.pop(0)
    
    if len(cols) >= 3:
        if not year_col and unassigned:
            year_col = unassigned.pop(0)
        if not dept_col and unassigned:
            dept_col = unassigned.pop(0)
    elif len(cols) == 2:
        if not dept_col and not year_col and unassigned:
            dept_col = unassigned.pop(0)

    return name_col, year_col, dept_col, id_col, email_col

def parse_records_from_dataframe(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Converts DataFrame to a list of dicts with 'name', 'year', 'department', optional 'cert_id', and 'email'."""
    name_col, year_col, dept_col, id_col, email_col = detect_columns(df)
    records = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else ""
        year = str(row[year_col]).strip() if year_col and pd.notna(row[year_col]) else ""
        dept = str(row[dept_col]).strip() if dept_col and pd.notna(row[dept_col]) else ""
        cid = str(row[id_col]).strip() if id_col and pd.notna(row[id_col]) else ""
        email = str(row[email_col]).strip() if email_col and pd.notna(row[email_col]) else ""
        
        if name and name.lower() not in ("nan", "none"):
            records.append({
                "name": name,
                "year": "" if year.lower() in ("nan", "none") else year,
                "department": "" if dept.lower() in ("nan", "none") else dept,
                "cert_id": "" if cid.lower() in ("nan", "none") else cid,
                "email": "" if email.lower() in ("nan", "none") else email
            })
    return records

def generate_cert_id(
    record: Dict[str, str],
    index: int,
    prefix: str = "GSA-FMC-2026-",
    mode: str = "sequential"
) -> str:
    """
    Generates a unique verification ID.
    If record already contains an explicit 'cert_id', uses that.
    Otherwise generates sequential (e.g. GSA-FMC-2026-001) or hash-based (e.g. GSA-FMC-2026-8A3D1E).
    """
    explicit = record.get("cert_id") or record.get("id") or record.get("certificate_id") or ""
    if explicit and explicit.strip() and explicit.lower() not in ("nan", "none", "-"):
        return explicit.strip()
    
    if mode == "hash":
        name = record.get("name", "")
        yr = record.get("year", "")
        dept = record.get("department", "")
        h = hashlib.sha256(f"{name}:{yr}:{dept}:{index}".encode("utf-8")).hexdigest()[:8].upper()
        return f"{prefix}{h}"
    else:
        return f"{prefix}{index:03d}"

def parse_records_from_file(file_path_or_buffer) -> List[Dict[str, str]]:
    """Loads CSV or Excel from file path or file-like object and extracts participant records."""
    name = getattr(file_path_or_buffer, "name", str(file_path_or_buffer))
    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(file_path_or_buffer)
    else:
        # CSV with delimiter detection
        try:
            df = pd.read_csv(file_path_or_buffer)
        except Exception:
            if hasattr(file_path_or_buffer, "seek"):
                file_path_or_buffer.seek(0)
            df = pd.read_csv(file_path_or_buffer, sep=None, engine="python")
    return parse_records_from_dataframe(df)

def parse_records_from_text(text: str) -> List[Dict[str, str]]:
    """
    Parses multi-line text where each line can be:
    - Name, Year, Department (3 values)
    - Name, Department
    - Name | Year | Department
    - Name (Year, Department)
    - Or just Name
    """
    records = []
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    for line in lines:
        # First check parentheses: Name (Year, Dept) or Name (Dept)
        m = re.match(r"^(.*?)\s*\((.*?)\)$", line)
        if m:
            name_part = m.group(1).strip()
            inside = m.group(2).strip()
            in_parts = [p.strip() for p in inside.split(",") if p.strip()]
            if len(in_parts) >= 2:
                records.append({"name": name_part, "year": in_parts[0], "department": in_parts[1]})
            else:
                p = in_parts[0] if in_parts else inside
                if any(k in p.lower() for k in ["year", "yr", "1st", "2nd", "3rd", "4th"]):
                    records.append({"name": name_part, "year": p, "department": ""})
                else:
                    records.append({"name": name_part, "year": "", "department": p})
            continue

        delimiters = ["\t", "|", " - ", ","]
        found_parts = None
        for d in delimiters:
            if d in line:
                parts = [p.strip() for p in line.split(d)]
                if len(parts) >= 2 and parts[0]:
                    found_parts = parts
                    break
        
        if found_parts:
            if len(found_parts) >= 3:
                records.append({
                    "name": found_parts[0],
                    "year": found_parts[1],
                    "department": found_parts[2]
                })
            elif len(found_parts) == 2:
                # Check if second part looks like a year
                p2 = found_parts[1]
                if any(k in p2.lower() for k in ["year", "yr", "1st", "2nd", "3rd", "4th"]) or p2 in ("I", "II", "III", "IV", "1", "2", "3", "4"):
                    records.append({"name": found_parts[0], "year": p2, "department": ""})
                else:
                    records.append({"name": found_parts[0], "year": "", "department": p2})
        else:
            records.append({"name": line, "year": "", "department": ""})
    return records

def clean_template_background(template_path: str = DEFAULT_TEMPLATE, output_path: str = CLEAN_TEMPLATE) -> str:
    """
    Seamlessly cleans the placeholder text '[Participant Name] of [Department / Section]'
    from the original template by vertically interpolating the smooth background.
    """
    if os.path.exists(output_path):
        return output_path

    img = Image.open(template_path).convert("RGB")
    pixels = img.load()

    # The placeholder text is between y: 406 and 440, and x: 340 and 840
    # Row 405 (above text) and row 442 (below text, above underline at 460)
    # contain the pristine background gradient.
    y_start = 405
    y_end = 442
    x_start = 340
    x_end = 840

    for x in range(x_start, x_end):
        top_color = pixels[x, y_start]
        bottom_color = pixels[x, y_end]
        for y in range(y_start + 1, y_end):
            ratio = (y - y_start) / (y_end - y_start)
            r = int((1.0 - ratio) * top_color[0] + ratio * bottom_color[0])
            g = int((1.0 - ratio) * top_color[1] + ratio * bottom_color[1])
            b = int((1.0 - ratio) * top_color[2] + ratio * bottom_color[2])
            pixels[x, y] = (r, g, b)

    img.save(output_path, "PNG")
    return output_path

class CertificateGenerator:
    def __init__(self, template_path: Optional[str] = None):
        base_dir = Path(__file__).parent.resolve()
        if template_path is None:
            cleaned = base_dir / CLEAN_TEMPLATE
            if not cleaned.exists():
                original = base_dir / DEFAULT_TEMPLATE
                if not original.exists():
                    raise FileNotFoundError(f"Template not found at {original}")
                clean_template_background(str(original), str(cleaned))
            self.template_path = str(cleaned)
        else:
            self.template_path = template_path

        self._base_template = Image.open(self.template_path).convert("RGB")

    def _get_font(self, font_path: str, size: int):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            return ImageFont.load_default()

    def format_participant_text(
        self,
        name: str,
        department: str = "",
        year: str = "",
        custom_format: str = "{name} of {year}, {department}"
    ) -> str:
        """Format the name, year, and department with graceful fallbacks."""
        name = str(name).strip()
        dept = str(department).strip() if department and str(department).lower() not in ("nan", "none", "-") else ""
        yr = str(year).strip() if year and str(year).lower() not in ("nan", "none", "-") else ""

        if not dept and not yr:
            return name
        
        # If the template specifically uses both {year} and {department}
        # handle missing components cleanly
        if "{year}" in custom_format and "{department}" in custom_format:
            if yr and not dept:
                # E.g. "{name} of {year}"
                fmt = custom_format.replace(", {department}", "").replace("{department}", "").strip()
                return fmt.format(name=name, year=yr, department="")
            elif dept and not yr:
                # E.g. "{name} of {department}"
                fmt = custom_format.replace("{year}, ", "").replace("{year} ", "").replace("{year}", "").strip()
                return fmt.format(name=name, year="", department=dept)

        try:
            res = custom_format.format(name=name, year=yr, department=dept)
            # Clean up potential double commas or awkward spacing
            res = re.sub(r",\s*,", ",", res)
            res = re.sub(r"of\s*,\s*", "of ", res)
            res = re.sub(r",\s*$", "", res)
            res = re.sub(r"\s{2,}", " ", res).strip()
            return res
        except Exception:
            if yr and dept:
                return f"{name} of {yr}, {dept}"
            elif dept:
                return f"{name} of {dept}"
            elif yr:
                return f"{name} of {yr}"
            return name

    def render_certificate(
        self,
        name: str,
        department: str = "",
        year: str = "",
        cert_id: Optional[str] = None,
        font_size: int = 24,
        prefer_bold: bool = True,
        font_path: Optional[str] = None,
        text_color: Tuple[int, int, int] = (32, 33, 36),
        y_offset: int = 0,
        custom_format: str = "{name} of {year}, {department}",
        max_width: int = 650
    ) -> Image.Image:
        """
        Renders a single personalized certificate image.
        Auto-shrinks font size if text exceeds max_width to keep it properly framed.
        Optionally renders a subtle unique verification ID centered at the bottom margin.
        """
        img = self._base_template.copy()
        draw = ImageDraw.Draw(img)

        full_text = self.format_participant_text(name, department, year, custom_format)
        
        selected_font_path = font_path or get_font_path(prefer_bold=prefer_bold)
        current_size = font_size

        # Fit text to line width
        font = self._get_font(selected_font_path, current_size)
        bbox = draw.textbbox((0, 0), full_text, font=font)
        text_w = bbox[2] - bbox[0]

        while text_w > max_width and current_size > 14:
            current_size -= 1
            font = self._get_font(selected_font_path, current_size)
            bbox = draw.textbbox((0, 0), full_text, font=font)
            text_w = bbox[2] - bbox[0]

        text_h = bbox[3] - bbox[1]

        # Center horizontally at the certificate center (590px for 1180px width)
        center_x = TEMPLATE_WIDTH // 2
        text_x = center_x - (text_w // 2)
        # Position baseline above the underline (y=460)
        text_y = (UNDERLINE_Y - text_h - 14) + y_offset

        draw.text((text_x, text_y), full_text, font=font, fill=text_color)

        # Render Verification / Certificate ID at the bottom margin
        if cert_id:
            id_font_path = get_font_path(prefer_bold=False, weight="regular")
            id_font = self._get_font(id_font_path, 12)
            id_text = f"Certificate ID: {cert_id}" if not str(cert_id).lower().startswith("cert") and not str(cert_id).lower().startswith("id:") else str(cert_id)
            id_bbox = draw.textbbox((0, 0), id_text, font=id_font)
            id_w = id_bbox[2] - id_bbox[0]
            # Center at bottom margin (y=804), above the bottom border
            draw.text((TEMPLATE_WIDTH // 2 - id_w // 2, 804), id_text, font=id_font, fill=(100, 105, 115))

        return img

    def generate_single_pdf(
        self,
        img: Image.Image,
        output_pdf_path: str
    ) -> str:
        """Saves a PIL image as a high-quality single-page PDF."""
        img.convert("RGB").save(output_pdf_path, "PDF", resolution=150.0)
        return output_pdf_path

    def batch_generate(
        self,
        records: List[Dict[str, str]],
        output_dir: str,
        export_png: bool = True,
        export_pdf: bool = False,
        merged_pdf_name: Optional[str] = None,
        enable_id: bool = True,
        id_prefix: str = "GSA-FMC-2026-",
        id_mode: str = "sequential",
        font_size: int = 24,
        prefer_bold: bool = True,
        custom_format: str = "{name} of {year}, {department}",
        progress_callback = None
    ) -> Dict[str, any]:
        """
        Batch generate certificates for a list of records [{'name': ..., 'year': ..., 'department': ...}].
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        generated_images = []
        generated_pngs = []
        generated_pdfs = []
        total = len(records)

        for i, rec in enumerate(records):
            name = str(rec.get("name", "")).strip()
            year = str(rec.get("year", "")).strip()
            dept = str(rec.get("department", "")).strip()
            if not name:
                continue

            parts = [p for p in [name, year, dept] if p]
            safe_suffix = "_".join(parts)
            safe_name = re.sub(r'[\\/*?:"<>|]', "", safe_suffix).strip().replace(" ", "_")[:60]
            if not safe_name:
                safe_name = f"certificate_{i+1}"

            cid = generate_cert_id(rec, i + 1, prefix=id_prefix, mode=id_mode) if enable_id else None

            cert_img = self.render_certificate(
                name=name,
                department=dept,
                year=year,
                cert_id=cid,
                font_size=font_size,
                prefer_bold=prefer_bold,
                custom_format=custom_format
            )

            if export_png:
                png_file = out_path / f"{safe_name}.png"
                cert_img.save(str(png_file), "PNG")
                generated_pngs.append(str(png_file))

            if export_pdf:
                pdf_file = out_path / f"{safe_name}.pdf"
                self.generate_single_pdf(cert_img, str(pdf_file))
                generated_pdfs.append(str(pdf_file))

            # Automatically log to registry
            try:
                from registry import log_certificate_record
                log_certificate_record(
                    cert_id=cid or f"CERT-{i+1}",
                    name=name,
                    year=year,
                    department=dept,
                    email=rec.get("email", ""),
                    delivery_status="Generated",
                    pdf_path=str(out_path / f"{safe_name}.pdf") if export_pdf else "",
                    png_path=str(out_path / f"{safe_name}.png") if export_png else ""
                )
            except Exception as log_err:
                print(f"Registry log warning: {log_err}")

            if merged_pdf_name:
                generated_images.append(cert_img)

            if progress_callback:
                progress_callback(i + 1, total)

        merged_pdf_path = None
        if merged_pdf_name and generated_images:
            merged_pdf_path = str(out_path / merged_pdf_name)
            first_img = generated_images[0]
            other_imgs = generated_images[1:] if len(generated_images) > 1 else []
            first_img.save(
                merged_pdf_path,
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=other_imgs
            )

        return {
            "total_processed": total,
            "png_count": len(generated_pngs),
            "pdf_count": len(generated_pdfs),
            "png_files": generated_pngs,
            "pdf_files": generated_pdfs,
            "merged_pdf": merged_pdf_path
        }
