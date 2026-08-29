import os
import io
import zipfile
import pandas as pd
import streamlit as st
from pathlib import Path
from certificate_engine import (
    CertificateGenerator,
    parse_records_from_dataframe,
    parse_records_from_file,
    parse_records_from_text,
    generate_cert_id,
    detect_columns,
    DEFAULT_TEMPLATE,
    CLEAN_TEMPLATE
)

st.set_page_config(
    page_title="Bulk Certificate Generator",
    page_icon="🎓",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1A73E8;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #5F6368;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

generator = CertificateGenerator()

st.markdown('<div class="main-header">🎓 Bulk Certificate Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Fund My Crazy: Build Night Edition • Google Student Ambassador Program 2026</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Typography & Layout")
    font_size = st.slider("Font Size", min_value=16, max_value=36, value=24, step=1)
    font_weight = st.selectbox("Font Weight", ["Bold (Google Sans)", "Regular (Google Sans)"], index=0)
    prefer_bold = ("Bold" in font_weight)
    y_offset = st.slider("Vertical Offset (px)", min_value=-20, max_value=20, value=0, step=1,
                         help="Adjust text position up (-) or down (+) relative to the underline.")
    
    custom_format = st.text_input(
        "Text Format Pattern",
        value="{name} of {year}, {department}",
        help="Use {name}, {year}, and {department}. If year or department is omitted in data, it adapts automatically."
    )

    st.divider()
    st.header("🆔 Verification ID")
    enable_id = st.checkbox("Append Unique Certificate ID", value=True, help="Renders a unique ID at the bottom margin.")
    if enable_id:
        id_prefix = st.text_input("ID Prefix", value="GSA-FMC-2026-")
        id_style = st.selectbox("ID Format", ["Sequential (001)", "Tamper-Proof Hash"], index=0)
        id_mode = "hash" if "Hash" in id_style else "sequential"
    else:
        id_prefix = "GSA-FMC-2026-"
        id_mode = "sequential"
    
    st.divider()
    st.header("📦 Output Formats")
    export_png = st.checkbox("Export individual PNG files", value=True)
    export_pdf = st.checkbox("Export individual PDF files", value=False)
    merge_pdf = st.checkbox("Export single merged multi-page PDF", value=True)

# Main Body: Input Tabs
input_tab1, input_tab2, input_tab3 = st.tabs(["📁 Upload File (CSV / Excel)", "✏️ Paste Names, Year & Dept", "📋 Sample Data"])

records = []

with input_tab1:
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel (.xlsx) file",
        type=["csv", "xlsx", "xls"],
        help="Columns detected: Name, Year, and Department (or Section/Dept/Branch)."
    )
    if uploaded_file is not None:
        try:
            records = parse_records_from_file(uploaded_file)
            if records:
                st.success(f"Successfully loaded {len(records)} participants from `{uploaded_file.name}`")
                preview_df = pd.DataFrame(records)
                st.dataframe(preview_df.head(10), use_container_width=True)
            else:
                st.warning("No valid participant records found in the file. Please check column headers.")
        except Exception as e:
            st.error(f"Error parsing file: {e}")

with input_tab2:
    pasted_text = st.text_area(
        "Paste participants (one per line)",
        height=150,
        placeholder="Aarav Sharma, III Year, Department of AI & DS\nPriya Ramesh, IV Year, Computer Science and Engineering\nKarthik Raja S, II Year, Information Technology"
    )
    if pasted_text.strip():
        text_records = parse_records_from_text(pasted_text)
        if text_records:
            records = text_records
            st.info(f"Loaded {len(records)} participants from pasted text.")
            st.dataframe(pd.DataFrame(records).head(5), use_container_width=True)

with input_tab3:
    st.write("Test the generator instantly with pre-populated sample participants (including Year):")
    if st.button("Load Sample Dataset (6 Participants)"):
        sample_path = Path("participants_sample.csv")
        if sample_path.exists():
            records = parse_records_from_file(str(sample_path))
            st.session_state["sample_records"] = records
        else:
            st.error("Sample file not found.")

if "sample_records" in st.session_state and not records:
    records = st.session_state["sample_records"]
    st.info(f"Loaded {len(records)} sample participants.")
    st.dataframe(pd.DataFrame(records), use_container_width=True)

# Live Preview & Batch Generation
if records:
    st.divider()
    col_prev_ctrl, col_prev_view = st.columns([1, 2])
    
    with col_prev_ctrl:
        st.subheader("👁️ Real-Time Preview")
        preview_names = []
        for i, r in enumerate(records):
            extra = " • ".join([x for x in [r.get("year", ""), r.get("department", "")] if x])
            preview_names.append(f"{i+1}. {r['name']}" + (f" ({extra})" if extra else ""))

        selected_idx = st.selectbox("Select participant to preview:", range(len(records)), format_func=lambda i: preview_names[i])
        
        selected_rec = records[selected_idx]
        preview_cid = generate_cert_id(selected_rec, selected_idx + 1, prefix=id_prefix, mode=id_mode) if enable_id else None

        preview_img = generator.render_certificate(
            name=selected_rec["name"],
            department=selected_rec.get("department", ""),
            year=selected_rec.get("year", ""),
            cert_id=preview_cid,
            font_size=font_size,
            prefer_bold=prefer_bold,
            y_offset=y_offset,
            custom_format=custom_format
        )
        
        formatted_preview_text = generator.format_participant_text(
            name=selected_rec["name"],
            department=selected_rec.get("department", ""),
            year=selected_rec.get("year", ""),
            custom_format=custom_format
        )
        st.markdown(f"**Rendered Text:** `{formatted_preview_text}`")
        if preview_cid:
            st.markdown(f"**Verification ID:** `{preview_cid}`")
        st.caption("Tip: Use the sidebar controls to adjust size, weight, and vertical position.")
        
    with col_prev_view:
        st.image(preview_img, caption="Live Certificate Preview", use_container_width=True)

    st.divider()
    st.subheader(f"🚀 Batch Generation ({len(records)} Certificates)")

    if st.button("✨ Generate All Certificates", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_progress(current, total):
            progress_bar.progress(current / total)
            status_text.text(f"Generating certificate {current} of {total}...")

        output_dir = "generated_certificates"
        merged_pdf_name = "all_certificates.pdf" if merge_pdf else None

        results = generator.batch_generate(
            records=records,
            output_dir=output_dir,
            export_png=export_png,
            export_pdf=export_pdf,
            merged_pdf_name=merged_pdf_name,
            enable_id=enable_id,
            id_prefix=id_prefix,
            id_mode=id_mode,
            font_size=font_size,
            prefer_bold=prefer_bold,
            custom_format=custom_format,
            progress_callback=update_progress
        )

        status_text.empty()
        progress_bar.progress(1.0)
        st.balloons()
        st.success(f"🎉 Successfully generated certificates for all {results['total_processed']} participants!")
        st.info(f"📁 Certificates are also saved locally in the folder: `{os.path.abspath(output_dir)}`")

        # Create in-memory ZIP package for download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for png in results["png_files"]:
                zf.write(png, arcname=f"png/{Path(png).name}")
            for pdf in results["pdf_files"]:
                zf.write(pdf, arcname=f"pdf/{Path(pdf).name}")
            if results["merged_pdf"]:
                zf.write(results["merged_pdf"], arcname=Path(results["merged_pdf"]).name)

        zip_buffer.seek(0)

        # Download buttons
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="⬇️ Download All as ZIP Archive",
                data=zip_buffer,
                file_name="certificates_bundle.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        if results["merged_pdf"] and os.path.exists(results["merged_pdf"]):
            with open(results["merged_pdf"], "rb") as f:
                pdf_bytes = f.read()
            with dl_col2:
                st.download_button(
                    label="📄 Download Merged Multi-Page PDF",
                    data=pdf_bytes,
                    file_name="all_certificates.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
else:
    st.info("👆 Please upload a CSV/Excel file, paste participants, or click 'Load Sample Dataset' to get started.")

