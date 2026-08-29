#!/usr/bin/env python3
"""
Bulk Certificate Generator CLI
Usage:
    python generate.py --input participants_sample.csv
    python generate.py --input participants_sample.xlsx --format both --merge-pdf all_certificates.pdf
"""

import argparse
import sys
from pathlib import Path
from certificate_engine import CertificateGenerator, parse_records_from_file

def main():
    parser = argparse.ArgumentParser(
        description="Generate bulk personalized certificates from CSV or Excel files."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to input CSV or Excel file containing participant details (Name, Department)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="generated_certificates",
        help="Directory where generated certificates will be saved. Default: ./generated_certificates"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["png", "pdf", "both"],
        default="png",
        help="Output format: 'png', 'pdf', or 'both'. Default: png"
    )
    parser.add_argument(
        "--merge-pdf",
        nargs="?",
        const="all_certificates.pdf",
        default=None,
        help="Also create a single merged multi-page PDF (e.g. --merge-pdf or --merge-pdf bundle.pdf)"
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=24,
        help="Base font size for the participant text. Default: 24"
    )
    parser.add_argument(
        "--bold",
        action="store_true",
        help="Use bold weight for the participant name/department."
    )
    parser.add_argument(
        "--text-format",
        default="{name} of {year}, {department}",
        help="Format pattern for participant line. Default: '{name} of {year}, {department}'"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading participant records from: {input_path}...")
    try:
        records = parse_records_from_file(input_path)
    except Exception as e:
        print(f"Error reading records from '{input_path}': {e}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print(f"No participant records found in '{input_path}'. Check file contents.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(records)} participant records.")

    print("Initializing certificate generator engine...")
    generator = CertificateGenerator()

    export_png = args.format in ("png", "both")
    export_pdf = args.format in ("pdf", "both")

    def print_progress(current, total):
        pct = (current / total) * 100
        bar = ("#" * int(pct // 4)).ljust(25, "-")
        print(f"\rGenerating: [{bar}] {current}/{total} ({pct:.0f}%)", end="", flush=True)

    print(f"Generating certificates into '{args.output_dir}'...")
    results = generator.batch_generate(
        records=records,
        output_dir=args.output_dir,
        export_png=export_png,
        export_pdf=export_pdf,
        merged_pdf_name=args.merge_pdf,
        font_size=args.font_size,
        prefer_bold=args.bold,
        custom_format=args.text_format,
        progress_callback=print_progress
    )
    print("\n")
    print("========================================")
    print("Certificate Generation Completed!")
    print(f"Total processed : {results['total_processed']}")
    if export_png:
        print(f"PNG files       : {results['png_count']} saved in {args.output_dir}")
    if export_pdf:
        print(f"PDF files       : {results['pdf_count']} saved in {args.output_dir}")
    if results["merged_pdf"]:
        print(f"Merged PDF      : {results['merged_pdf']}")
    print("========================================")

if __name__ == "__main__":
    main()

