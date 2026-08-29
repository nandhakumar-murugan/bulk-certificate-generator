# Bulk Certificate Generator
**Fund My Crazy: Build Night Edition • Google Student Ambassador Program 2026**

An automated bulk certificate generator tailored to produce personalized certificates from participant names and department details.

---

## 🌟 Features
- **Seamless Template Cleaning**: Automatically clears out placeholder text (`[Participant Name] of [Department / Section]`) from the template with zero visible artifacts or background distortion.
- **Multiple Input Methods**:
  - Upload CSV or Excel (`.xlsx`, `.xls`) files.
  - Paste name and department lists directly.
  - One-click sample dataset for immediate testing.
- **Interactive Web App (Streamlit)**:
  - Real-time live visual preview of any participant's certificate.
  - Adjust typography, font size, bold weight, and vertical position on the fly.
  - Progress bar during bulk generation.
  - Instant download buttons for individual PNGs/PDFs (ZIP archive) and a merged multi-page PDF.
- **Command-Line Interface (CLI)**:
  - Fast script for terminal automation and batch operations.
- **Automatic Text Scaling**:
  - Automatically scales down font size for long names or department titles so they never overflow the certificate guidelines.

---

## 🚀 Quick Start

### Method 1: Web Interface (Recommended)
You can launch the web application by double-clicking `run_app.bat` or by running:
```powershell
python -m streamlit run app.py
```
This opens your browser at `http://localhost:8501`.

### Method 2: Command-Line Interface (CLI)
To batch generate certificates directly from the terminal:

```powershell
# Generate PNG certificates from sample CSV
python generate.py --input participants_sample.csv

# Generate both PNG and PDF, plus a single combined multi-page PDF
python generate.py --input participants_sample.xlsx --format both --merge-pdf all_certificates.pdf

# Customize font size or make text bold
python generate.py --input participants_sample.csv --font-size 26 --bold
```

---

## 📄 Input File Format

Your CSV or Excel file can contain columns named `Name`, `Year`, and `Department` (case-insensitive).
Accepted header variations:
- **Name Column**: `Name`, `Participant`, `Student Name`, `Full Name`, `Attendee`
- **Year Column**: `Year`, `Yr`, `Academic Year`, `Class Year`, `Batch`, `Sem`
- **Department Column**: `Department`, `Dept`, `Section`, `Branch`, `Stream`

### Sample CSV format:
```csv
Name,Year,Department
Aarav Sharma,III Year,Department of AI & DS
Priya Ramesh,IV Year,Computer Science and Engineering
Karthik Raja S,II Year,Information Technology
Deepika Sundaram,III Year,Electronics & Communication Engg
Mohammed Farhan,II Year,School of Innovation (SOI)
```

If pasting text directly into the web app, you can use any of these formats:
```text
Aarav Sharma, III Year, Department of AI & DS
Priya Ramesh | IV Year | Computer Science and Engineering
Karthik Raja S (II Year, Information Technology)
Deepika Sundaram, III Year, ECE
```

---

## 📁 Output Structure
When you generate certificates, they are saved in the `generated_certificates/` folder:
```
generated_certificates/
  ├── Aarav_Sharma_Department_of_AI_&_DS.png
  ├── Aarav_Sharma_Department_of_AI_&_DS.pdf
  ├── Priya_Ramesh_Computer_Science_and_Engineering.png
  ├── all_certificates.pdf  (if merge option selected)
```
In the web interface, you can also download them all as a single `.zip` or a merged multi-page `.pdf`.

