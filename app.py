import hashlib
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape

from src.ai_explainer import (
    OllamaModelUnavailableError, OllamaUnavailableError,
    chat_about_measurements, explain_measurements,
)
from src.dashboard import apply_dashboard_style, show_dashboard_header, show_overview
from src.document_processor import extract_document_text
from src.report_extractor import extract_measurements
from src.report_comparison import compare_reports
from src.auth import (
    delete_saved_report,
    get_saved_report,
    list_saved_reports,
    save_report,
    show_authentication,
)
st.set_page_config(page_title="SWASTHYA AI", page_icon="🩺", layout="wide")
# Authentication
if not show_authentication():
    st.stop()
try:
    AI_ENABLED = str(st.secrets.get("AI_ENABLED", "true")).lower() == "true"
except StreamlitSecretNotFoundError:
    AI_ENABLED = True

apply_dashboard_style()
show_dashboard_header(AI_ENABLED)

pages = ["Overview", "Report Analysis", "Report Comparison"]
if AI_ENABLED:
    pages.append("AI Assistant")
page = st.sidebar.radio("Navigation", pages)
st.sidebar.caption("Educational assistance only. Not a medical diagnosis.")


def process_report_content(file_name, file_bytes):
    ext = file_name.rsplit(".", 1)[-1].lower()
    text = extract_document_text(file_bytes, ext)
    if not text or not text.strip():
        raise ValueError("No text extracted. Scanned PDFs/images may require OCR.")
    df = extract_measurements(text)
    if df is None or df.empty:
        raise ValueError("No supported measurements found. Check the extracted text.")
    return text, df


def process_report(upload):
    return process_report_content(upload.name, upload.getvalue())


def generate_pdf_report(
    measurements,
    report_name,
    explanation="",
    comparison=None,
    report_title="Medical Report",
):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#176B87"),
        alignment=1
    ))

    story = []

    story.append(
        Paragraph(
            f"SWASTHYA AI - {escape(report_title)}",
            styles["CustomTitle"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Report:</b> {escape(str(report_name))}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            styles["Normal"]
        )
    )

    if not measurements.empty:
        story.append(Spacer(1, 15))
        story.append(
            Paragraph("Extracted Medical Measurements", styles["Heading2"])
        )

        data = [[str(column) for column in measurements.columns]]
        for _, row in measurements.iterrows():
            data.append([
                str(value) if pd.notna(value) else "-"
                for value in row
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B87")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)

    if explanation:
        story.append(Spacer(1, 20))
        story.append(
            Paragraph("AI-Generated Explanation", styles["Heading2"])
        )

        for paragraph in explanation.split("\n"):
            if paragraph.strip():
                story.append(
                    Paragraph(
                        escape(paragraph),
                        styles["Normal"]
                    )
                )
                story.append(Spacer(1, 8))

    if comparison is not None and not comparison.empty:
        story.append(Spacer(1, 20))
        story.append(
            Paragraph("Medical Report Comparison", styles["Heading2"])
        )

        comparison_data = [
            [str(column) for column in comparison.columns]
        ]

        for _, row in comparison.iterrows():
            comparison_data.append([
                str(value) if pd.notna(value) else "-"
                for value in row
            ])

        comparison_table = Table(
            comparison_data,
            repeatRows=1
        )

        comparison_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B87")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))

        story.append(comparison_table)

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>Medical Disclaimer:</b> This report provides educational "
            "information only. It is not a medical diagnosis or a substitute "
            "for professional medical advice. Verify all extracted values "
            "against the original laboratory report.",
            styles["Normal"]
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()

if "analysis_measurements" not in st.session_state:
    st.session_state.analysis_measurements = pd.DataFrame()
    st.session_state.analysis_text = ""
    st.session_state.analysis_name = ""
    st.session_state.analysis_explanation = ""


if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if page == "Overview":
    show_overview(st.session_state.analysis_measurements)
    if st.session_state.analysis_name:
        st.caption(f"Loaded report: {st.session_state.analysis_name}")
    if st.session_state.get("comparison_result") is not None:
        st.subheader("Latest comparison")
        st.dataframe(st.session_state.comparison_result, use_container_width=True, hide_index=True)

elif page == "Report Analysis":
    st.subheader("🧪 Report Analysis")
    st.caption(
        "Upload a lab report to extract supported measurements, review the "
        "results, and download a copy for your records. Saved reports are "
        "encrypted at rest; connection security depends on the app's hosting."
    )
    try:
        saved_reports = list_saved_reports(st.session_state.user_id)
    except Exception as e:
        st.error(f"Could not load saved reports: {e}")
        saved_reports = []
    with st.expander("📁 Saved reports in your account"):
        if not saved_reports:
            st.info("No reports have been saved to this account yet.")
        for saved_report in saved_reports:
            download_col, delete_col = st.columns([4, 1])
            download_col.write(
                f"**{saved_report['filename']}**  \n"
                f"Saved: {saved_report['uploaded_at']}"
            )
            try:
                saved_file = get_saved_report(
                    st.session_state.user_id,
                    saved_report["id"],
                )
            except Exception as e:
                download_col.error(f"Could not read saved report: {e}")
            else:
                if saved_file is None:
                    download_col.error("This saved report is unavailable.")
                else:
                    saved_filename, saved_bytes = saved_file
                    download_col.download_button(
                        "Download",
                        data=saved_bytes,
                        file_name=saved_filename,
                        mime="application/octet-stream",
                        key=f"download_saved_report_{saved_report['id']}",
                    )
            if delete_col.button(
                "Delete",
                key=f"delete_saved_report_{saved_report['id']}",
            ):
                try:
                    delete_saved_report(
                        st.session_state.user_id,
                        saved_report["id"],
                    )
                except Exception as e:
                    st.error(f"Could not delete saved report: {e}")
                else:
                    st.rerun()
    upload_option = "upload_new"
    saved_report_by_id = {report["id"]: report for report in saved_reports}
    report_source = st.selectbox(
        "Report to analyze",
        [upload_option, *saved_report_by_id],
        format_func=lambda report_id: (
            "Upload a new report"
            if report_id == upload_option
            else saved_report_by_id[report_id]["filename"]
        ),
        key="analysis_report_source",
    )
    upload = None
    report_data = None
    if report_source == upload_option:
        upload = st.file_uploader(
            "Upload a laboratory report",
            type=["pdf", "png", "jpg", "jpeg"],
            key="analysis_upload",
        )
        if upload:
            report_data = (upload.name, upload.getvalue())
    else:
        try:
            report_data = get_saved_report(
                st.session_state.user_id,
                report_source,
            )
        except Exception as e:
            st.error(f"Could not load saved report: {e}")
        if report_data is None:
            st.error("The selected saved report is unavailable.")

    if report_data:
        report_name, report_bytes = report_data
        sig = hashlib.sha256(report_bytes).hexdigest()
        if upload:
            try:
                save_report(
                    st.session_state.user_id,
                    report_name,
                    report_bytes,
                )
            except Exception as e:
                st.error(f"Could not save uploaded report: {e}")
        if (
            st.session_state.get("analysis_signature") != sig
            or st.session_state.analysis_measurements.empty
        ):
            st.session_state.analysis_signature = None
            st.session_state.analysis_measurements = pd.DataFrame()
            st.session_state.analysis_text = ""
            st.session_state.analysis_name = ""
            st.session_state.analysis_explanation = ""
            st.session_state.chat_messages = []
            try:
                with st.spinner("Extracting report..."):
                    text, df = process_report_content(report_name, report_bytes)
            except Exception as e:
                st.error(f"Could not process report: {e}")
            else:
                st.session_state.analysis_signature = sig
                st.session_state.analysis_text = text
                st.session_state.analysis_measurements = df
                st.session_state.analysis_name = report_name
    df = st.session_state.analysis_measurements
    if not df.empty:
        with st.expander("View extracted report text"):
            st.text_area("Extracted text", st.session_state.analysis_text, height=220)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode("utf-8"), "extracted_medical_data.csv", "text/csv")
        try:
            pdf_data = generate_pdf_report(
                measurements=df,
                report_name=st.session_state.analysis_name,
                explanation=st.session_state.get("analysis_explanation", ""),
                comparison=st.session_state.get("comparison_result"),
            )
        except Exception as e:
            st.error(f"Could not generate PDF report: {e}")
        else:
            st.download_button(
                label="📄 Download Medical Report (PDF)",
                data=pdf_data,
                file_name="SWASTHYA_AI_Medical_Report.pdf",
                mime="application/pdf",
            )

        if AI_ENABLED:
            st.subheader("🤖 AI-Powered Medical Explanation")
            lang = st.selectbox("Explanation language", ["English", "Hindi", "Marathi"], key="analysis_lang")
            if st.button("Generate AI Explanation"):
                try:
                    with st.spinner("Generating explanation..."):
                        explanation = explain_measurements(df, lang)

                    st.session_state.analysis_explanation = explanation
                except (OllamaUnavailableError, OllamaModelUnavailableError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Could not generate explanation: {e}")
            explanation = st.session_state.get("analysis_explanation", "")
            if explanation:
                st.markdown(explanation)
                try:
                    explanation_pdf = generate_pdf_report(
                        measurements=pd.DataFrame(),
                        report_name=st.session_state.analysis_name,
                        explanation=explanation,
                        report_title="Medical Report Explanation",
                    )
                except Exception as e:
                    st.error(f"Could not generate explanation PDF: {e}")
                else:
                    st.download_button(
                        label="📄 Download Explanation (PDF)",
                        data=explanation_pdf,
                        file_name="SWASTHYA_AI_Explanation.pdf",
                        mime="application/pdf",
                    )

elif page == "Report Comparison":
    st.subheader("📊 Medical Report Comparison")
    st.caption(
        "See how extracted measurements differ between two reports. "
        "Units must be compatible for a numeric comparison."
    )
    try:
        saved_reports = list_saved_reports(st.session_state.user_id)
    except Exception as e:
        st.error(f"Could not load saved reports: {e}")
        saved_reports = []
    saved_report_by_id = {report["id"]: report for report in saved_reports}
    upload_new_option = "upload_new"
    report_options = [upload_new_option, *saved_report_by_id]

    def report_option_label(report_id):
        if report_id == upload_new_option:
            return "Upload a new report"
        report = saved_report_by_id[report_id]
        return f"{report['filename']} (saved {report['uploaded_at']})"

    previous_source = st.selectbox(
        "Previous report source",
        report_options,
        format_func=report_option_label,
        key="previous_report_source",
    )
    old_upload = None
    if previous_source == upload_new_option:
        old_upload = st.file_uploader(
            "Upload previous report",
            type=["pdf", "png", "jpg", "jpeg"],
            key="old_upload",
        )

    current_source = st.selectbox(
        "Current report source",
        report_options,
        format_func=report_option_label,
        key="current_report_source",
    )
    new_upload = None
    if current_source == upload_new_option:
        new_upload = st.file_uploader(
            "Upload current report",
            type=["pdf", "png", "jpg", "jpeg"],
            key="new_upload",
        )

    old_report = None
    new_report = None
    for selected_source, uploaded_file, label in (
        (previous_source, old_upload, "previous"),
        (current_source, new_upload, "current"),
    ):
        try:
            if selected_source == upload_new_option:
                if uploaded_file:
                    file_bytes = uploaded_file.getvalue()
                    save_report(
                        st.session_state.user_id,
                        uploaded_file.name,
                        file_bytes,
                    )
                    report_data = (uploaded_file.name, file_bytes)
                else:
                    report_data = None
            else:
                report_data = get_saved_report(
                    st.session_state.user_id,
                    selected_source,
                )
                if report_data is None:
                    raise ValueError("The selected saved report is unavailable.")
        except Exception as e:
            st.error(f"Could not load the {label} report: {e}")
            report_data = None

        if label == "previous":
            old_report = report_data
        else:
            new_report = report_data
    d1, d2 = st.columns(2)
    with d1:
        old_date = st.date_input("Previous report date", value=date.today(), key="old_date")
    with d2:
        new_date = st.date_input("Current report date", value=date.today(), key="new_date")
    if old_report and new_report:
        if new_date < old_date:
            st.warning("The current report date is earlier than the previous date. Please verify.")
        if st.button("Compare Reports"):
            try:
                with st.spinner("Comparing reports..."):
                    _, old_df = process_report_content(*old_report)
                    _, new_df = process_report_content(*new_report)
                    st.session_state.comparison_result = compare_reports(old_df, new_df)
                    st.session_state.comparison_dates = (str(old_date), str(new_date))
                    st.session_state.comparison_names = (
                        old_report[0],
                        new_report[0],
                    )
            except Exception as e:
                st.error(f"Could not compare reports: {e}")
    result = st.session_state.get("comparison_result")
    if result is not None:
        st.dataframe(result, use_container_width=True, hide_index=True)
        chart = result[(result["Match Status"] == "Matched") & result["Units Compatible"].fillna(False)].dropna(subset=["Previous Value", "Current Value"])
        if not chart.empty:
            chart = chart.melt(id_vars=["Test"], value_vars=["Previous Value", "Current Value"], var_name="Report", value_name="Value")
            st.plotly_chart(px.bar(chart, x="Test", y="Value", color="Report", barmode="group", title="Previous vs Current Values"), use_container_width=True)
        st.download_button("📥 Download comparison CSV", result.to_csv(index=False).encode("utf-8"), "medical_report_comparison.csv", "text/csv")
        comparison_names = st.session_state.get("comparison_names", ())
        comparison_report_name = " vs ".join(comparison_names) or "Report comparison"
        try:
            comparison_pdf = generate_pdf_report(
                measurements=pd.DataFrame(),
                report_name=comparison_report_name,
                comparison=result,
                report_title="Medical Report Comparison",
            )
        except Exception as e:
            st.error(f"Could not generate comparison PDF: {e}")
        else:
            st.download_button(
                label="📄 Download Comparison (PDF)",
                data=comparison_pdf,
                file_name="SWASTHYA_AI_Report_Comparison.pdf",
                mime="application/pdf",
            )
        st.caption("Numerical changes do not automatically indicate improvement or deterioration.")

elif page == "AI Assistant" and AI_ENABLED:
    st.subheader("💬 Chat with Your Medical Report")
    st.caption(
        "Ask questions about values extracted from your latest report. "
        "Responses are educational and are not a medical diagnosis."
    )
    df = st.session_state.analysis_measurements
    if df.empty:
        st.info("First upload a report in Report Analysis.")
    else:
        st.caption(f"Report context: {st.session_state.analysis_name}")
        lang = st.selectbox("Response language", ["English", "Hindi", "Marathi"], key="chat_lang")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        question = st.chat_input("Ask a question about your report...")
        if question:
            with st.chat_message("user"):
                st.markdown(question)
            try:
                with st.spinner("SWASTHYA AI is thinking..."):
                    answer = chat_about_measurements(df, question, st.session_state.chat_messages, lang)
                st.session_state.chat_messages.extend([
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": answer},
                ])
                with st.chat_message("assistant"):
                    st.markdown(answer)
            except (OllamaUnavailableError, OllamaModelUnavailableError) as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Could not generate a response: {e}")
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()

st.divider()
st.caption("SWASTHYA AI provides educational information only. Verify extracted values, units, dates, and reference ranges against the original reports. It is not a diagnosis or a substitute for professional care.")
