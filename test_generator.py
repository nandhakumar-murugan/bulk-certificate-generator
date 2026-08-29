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

    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()

