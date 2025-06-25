import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pandas as pd
from io import BytesIO

import streamlit as st
import tempfile
import json

from utils.extract_text import extract_text
from utils.ocr_utils import extract_text_from_scanned_pdf
from utils.metadata_utils import generate_metadata

st.set_page_config(page_title="Metadata Generator", layout="wide")
st.title("Automated Meta Data Generator")

uploaded_file = st.file_uploader("Upload your document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

if uploaded_file:
    file_name = uploaded_file.name
    ext = os.path.splitext(file_name)[1].lower()

    use_ocr = False
    if ext == ".pdf":
        use_ocr = st.checkbox("Force OCR for scanned PDFs?", value=False)

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    # Text extraction logic
    st.info("Extracting text from document...")
    if use_ocr:
        text = extract_text_from_scanned_pdf(tmp_file_path)
    else:
        text = extract_text(tmp_file_path)
        if len(text.strip()) < 5:
            st.warning("Text too short or empty, trying OCR fallback...")
            text = extract_text_from_scanned_pdf(tmp_file_path)

    st.success("Text extracted sucessfully.")
    st.subheader("Text Preview")
    st.text_area("Extracted Document Text", value=text[:1500], height=250)

    # Metadata button
    if st.button("Generate Meta Data"):
        metadata = generate_metadata(text)

        st.subheader("Extracted Metadata:  ")

        # Title
        st.markdown(f"### 🏷️ Title:\n**{metadata.get('title', 'N/A')}**")

    
        # Expandable Sections
        for field in ["abstract", "objectives", "methodology", "results", "conclusion"]:
            content = metadata.get(field)
            if content and len(content.strip()) > 0:
                with st.expander(f"📘 {field.capitalize()}"):
                    st.markdown(content)
        
        # Horizontal layout
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**👥 Authors**")
            authors = metadata.get("authors", [])
            if authors:
              with st.expander("Show Authors"):
                 for name in authors:
                    st.markdown(f"- {name}")
            else:
              st.markdown("N/A")

        with col2:
            st.markdown("**🔑 Keywords**")
            keywords = metadata.get("keywords", [])
            if keywords:
              with st.expander("Show Keywords"):
                for kw in keywords:
                   st.markdown(f"- {kw}")
            else:
              st.markdown("N/A")

        with col3:
            st.markdown("**🧰 Algorithm and Tools Used**")
            algorithms = metadata.get("algorithms", [])
            if algorithms:
              with st.expander("Show Algo & Tools"):
                for kw in algorithms:
                   st.markdown(f"- {kw}")
            else:
              st.markdown("N/A")
        
        
        # Language and Read time
        col4, col5 = st.columns(2)
        with col4:
            st.markdown(f"**🈶 Language**: {metadata.get('language', 'N/A')}")
        with col5:
            st.markdown(f"**⏱️Est. Read Time**: {metadata.get('read_time', 'N/A')}")

        # JSON Download
        json_str = json.dumps(metadata, indent=4)
        st.download_button("📥 Download Metadata (JSON)", data=json_str, file_name="metadata.json", mime="application/json")
        
        # Excel Export
        excel_buffer = BytesIO()
        df = pd.DataFrame([metadata])  
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        st.download_button(
        label="📊 Download Metadata (Excel)",
        data=excel_buffer.getvalue(),
        file_name="metadata.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

