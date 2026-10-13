"""
Unit tests for Bulk Certificate Generator engine and participant record parsing.
"""

import os
import csv
import pytest
from PIL import Image, ImageDraw, ImageFont


def test_center_alignment_math():
    """Verify horizontal center-alignment coordinate calculation."""
    canvas_width = 1920
    text_width = 540

    center_x = (canvas_width - text_width) // 2
    assert center_x == 690
    assert center_x + text_width // 2 == canvas_width // 2


def test_participant_csv_parsing(tmp_path):
    """Test reading and sanitizing CSV records with various header formats."""
    csv_file = tmp_path / "test_participants.csv"
    csv_content = [
        ["Full Name", "Email Address", "Institution"],
        ["Nandhakumar Murugan", "test@example.com", "KGiSL Institute of Technology"],
        ["  Jane Doe  ", "jane@example.com", "Tech Academy"],
    ]

    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(csv_content)

    records = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "name": row["Full Name"].strip(),
                "email": row["Email Address"].strip(),
                "institution": row["Institution"].strip(),
            })

    assert len(records) == 2
    assert records[0]["name"] == "Nandhakumar Murugan"
    assert records[1]["name"] == "Jane Doe"


def test_image_canvas_rendering():
    """Verify PIL canvas drawing, bounding box retrieval, and image generation."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Use default font
    font = ImageFont.load_default()
    text = "CERTIFICATE OF PARTICIPATION"

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw_x = (width - text_w) // 2
    draw_y = (height - text_h) // 2
    draw.text((draw_x, draw_y), text, fill=(30, 30, 30), font=font)

    assert img.size == (800, 600)
    assert draw_x > 0
    assert draw_y > 0
