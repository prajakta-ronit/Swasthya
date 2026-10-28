import streamlit as st

from src.document_processor import extract_document_text


st.set_page_config(
    page_title="SWASTHYA AI",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 SWASTHYA AI")
st.subheader("AI-Powered Medical Report Analyzer")

st.write(
    "Upload a laboratory report to extract its text "
    "and prepare it for structured analysis."
)

uploaded_file = st.file_uploader(
    "Upload a medical report",
    type=["pdf", "png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    try:
        with st.spinner("Extracting document text..."):
            extracted_text = extract_document_text(
                file_bytes,
                file_extension
            )

        if extracted_text:
            st.success("Document text extracted successfully.")

            st.subheader("Extracted Text")
            st.text_area(
                "Document contents",
                value=extracted_text,
                height=350
            )

            st.info(
                "The extracted text has not yet been clinically "
                "validated or interpreted."
            )
        else:
            st.warning(
                "No embedded text was found. This may be a scanned "
                "PDF requiring OCR processing."
            )

    except Exception as error:
        st.error(f"Document processing failed: {error}")