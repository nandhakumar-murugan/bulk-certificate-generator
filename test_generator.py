"""
Verification Test Script for Bulk Certificate Generator
"""
import os
from pathlib import Path
from certificate_engine import (
    CertificateGenerator,
    parse_records_from_file,
    parse_records_from_text
)

def run_tests():
    print("Test 1: Testing text parser with Name, Year, Department...")
    raw_text = """
    Aarav Sharma, III Year, Department of AI & DS
    Priya Ramesh | IV Year | Computer Science
    Karthik Raja (II Year, Information Technology)
    John Doe - Mechanical
    Simple Name Without Dept
    """
    records = parse_records_from_text(raw_text)
    assert len(records) == 5, f"Expected 5 records, got {len(records)}"
    assert records[0]["name"] == "Aarav Sharma" and records[0]["year"] == "III Year" and records[0]["department"] == "Department of AI & DS"
    assert records[1]["name"] == "Priya Ramesh" and records[1]["year"] == "IV Year" and records[1]["department"] == "Computer Science"
    assert records[2]["name"] == "Karthik Raja" and records[2]["year"] == "II Year" and records[2]["department"] == "Information Technology"
    assert records[3]["name"] == "John Doe" and records[3]["department"] == "Mechanical"
    assert records[4]["name"] == "Simple Name Without Dept" and records[4]["department"] == ""
    print("  -> Passed!")

    print("Test 2: Testing parser with CSV and Excel...")
    csv_records = parse_records_from_file("participants_sample.csv")
    excel_records = parse_records_from_file("participants_sample.xlsx")
    assert len(csv_records) == 6, f"Expected 6 records in CSV, got {len(csv_records)}"
    assert len(excel_records) == 6, f"Expected 6 records in Excel, got {len(excel_records)}"
    print("  -> Passed!")

    print("Test 3: Initializing Certificate Generator...")
    gen = CertificateGenerator()
    print("  -> Template cleaned and loaded successfully!")

    print("Test 4: Batch generation with PNG, PDF, and Merged PDF...")
    output_dir = "test_output"
    results = gen.batch_generate(
        records=csv_records[:3],
        output_dir=output_dir,
        export_png=True,
        export_pdf=True,
        merged_pdf_name="test_merged.pdf",
        font_size=24,
        prefer_bold=False
    )

    assert results["total_processed"] == 3
    assert results["png_count"] == 3
    assert results["pdf_count"] == 3
    assert results["merged_pdf"] is not None and os.path.exists(results["merged_pdf"])
    print("  -> Passed! Generated 3 PNGs, 3 PDFs, and 1 Merged PDF.")

    print("Test 5: Testing long name auto-scaling...")
    long_img = gen.render_certificate(
        name="Alexander Bartholomew Montgomery-Higginbotham III",
        department="Department of Advanced Robotics and Artificial Intelligence Research",
        font_size=28
    )
    long_img_path = Path(output_dir) / "long_name_test.png"
    long_img.save(str(long_img_path))
    assert long_img_path.exists()
    print("  -> Passed! Long name scaled and rendered.")

    print("Test 6: Testing bundled Google Sans font fidelity...")
    from certificate_engine import get_font_path, FONT_GOOGLE_SANS_BOLD, FONT_GOOGLE_SANS_REGULAR
    bold_path = get_font_path(prefer_bold=True)
    reg_path = get_font_path(prefer_bold=False)
    assert "GoogleSans-Bold.ttf" in bold_path, f"Expected GoogleSans-Bold, got {bold_path}"
    assert "GoogleSans-Regular.ttf" in reg_path, f"Expected GoogleSans-Regular, got {reg_path}"
    print(f"  -> Passed! Bundled fonts loaded: {bold_path}")

    print("Test 7: Testing Unique Verification ID (Sequential & Hash)...")
    from certificate_engine import generate_cert_id
    sample_rec = {"name": "Aarav Sharma", "year": "III Year", "department": "AI & DS"}
    seq_id = generate_cert_id(sample_rec, 1, prefix="GSA-FMC-2026-", mode="sequential")
    hash_id = generate_cert_id(sample_rec, 1, prefix="GSA-FMC-2026-", mode="hash")
    assert seq_id == "GSA-FMC-2026-001", f"Unexpected sequential ID: {seq_id}"
    assert hash_id.startswith("GSA-FMC-2026-") and len(hash_id) == len("GSA-FMC-2026-") + 8, f"Unexpected hash ID: {hash_id}"
    
    cert_with_id = gen.render_certificate(
        name=sample_rec["name"],
        department=sample_rec["department"],
        year=sample_rec["year"],
        cert_id=seq_id
    )
    cert_id_path = Path(output_dir) / "cert_with_id.png"
    cert_with_id.save(str(cert_id_path))
    assert cert_id_path.exists()
    print(f"  -> Passed! Sequential: {seq_id}, Hash: {hash_id}")

    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()

