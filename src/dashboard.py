import pandas as pd
import streamlit as st
import plotly.express as px


def apply_dashboard_style():
    """Apply a polished, responsive visual theme to SWASTHYA AI."""

    st.markdown(
        """
        <style>
        :root {
            --sw-primary: #087e8b;
            --sw-primary-dark: #075b66;
            --sw-ink: #14324b;
            --sw-muted: #607789;
            --sw-border: #dce8ed;
            --sw-surface: #ffffff;
        }

        .stApp {
            background:
                radial-gradient(ellipse at 75% 0%, rgba(221, 242, 240, 0.62), transparent 34rem),
                #f4f8fa;
            color: var(--sw-ink);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #edf6f6 0%, #f3f7fa 100%);
            border-right: 1px solid var(--sw-border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.4rem;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }

        .dashboard-title {
            font-size: clamp(1.7rem, 3vw, 2.35rem);
            font-weight: 800;
            letter-spacing: -0.045em;
            color: var(--sw-ink);
            margin-bottom: 0.3rem;
        }

        .dashboard-subtitle {
            color: var(--sw-muted);
            font-size: 1rem;
            margin-bottom: 1.8rem;
        }

        .dashboard-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.7rem;
            border: 1px solid #cce5e2;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            color: var(--sw-primary-dark);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin-bottom: 0.7rem;
        }

        .section-heading {
            color: var(--sw-ink);
            font-size: 1.4rem;
            font-weight: 750;
            letter-spacing: -0.025em;
            margin-top: 1.2rem;
            margin-bottom: 1rem;
        }

        div[data-testid="stMetric"] {
            background: var(--sw-surface);
            border: 1px solid var(--sw-border);
            padding: 1.15rem 1.25rem;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(20, 50, 75, 0.045);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(20, 50, 75, 0.08);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--sw-muted);
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: var(--sw-ink);
            font-weight: 750;
        }

        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--sw-border);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius: 10px;
            transition: background-color 140ms ease;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            background: rgba(8, 126, 139, 0.08);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: rgba(8, 126, 139, 0.12);
        }

        [data-testid="stFileUploader"] section {
            border: 1px dashed #9bbdc4;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.72);
        }

        [data-testid="stFileUploader"] section:hover {
            border-color: var(--sw-primary);
            background: #f7fcfc;
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 2.7rem;
            border-radius: 10px;
            font-weight: 650;
            transition: transform 140ms ease, box-shadow 140ms ease;
        }

        .stButton > button[kind="primary"] {
            border-color: var(--sw-primary);
            background: var(--sw-primary);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 5px 14px rgba(8, 126, 139, 0.14);
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--sw-border);
            border-radius: 12px;
            overflow: hidden;
        }

        .overview-empty {
            padding: clamp(1.2rem, 3vw, 2rem);
            border: 1px solid var(--sw-border);
            border-radius: 18px;
            background: linear-gradient(130deg, #ffffff 12%, #f1f8f8 100%);
            box-shadow: 0 12px 32px rgba(20, 50, 75, 0.045);
        }

        .overview-empty h3 {
            margin: 0 0 0.45rem;
            color: var(--sw-ink);
            font-size: 1.25rem;
        }

        .overview-empty p {
            margin: 0;
            color: var(--sw-muted);
            line-height: 1.65;
        }

        .overview-steps {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1.3rem;
        }

        .overview-step {
            padding: 1rem;
            border: 1px solid var(--sw-border);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.78);
        }

        .overview-step strong {
            display: block;
            margin-bottom: 0.3rem;
            color: var(--sw-ink);
        }

        .overview-step span {
            color: var(--sw-muted);
            font-size: 0.9rem;
            line-height: 1.5;
        }

        @media (max-width: 700px) {
            .block-container {
                padding: 1.2rem 1rem 2rem;
            }

            .overview-steps {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_dashboard_header(ai_enabled: bool = True):
    """Display the dashboard heading."""

    st.markdown(
        '<div class="dashboard-eyebrow">YOUR HEALTH REPORT, MADE CLEARER</div>'
        '<div class="dashboard-title">🩺 SWASTHYA AI</div>',
        unsafe_allow_html=True,
    )

    subtitle = (
        "AI-Powered Medical Report Analysis & Health Insights"
        if ai_enabled
        else "Medical Report Analysis & Health Insights"
    )
    st.markdown(
        f'<div class="dashboard-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def show_overview(measurements: pd.DataFrame):
    """Display summary metrics and charts for extracted results."""

    st.markdown(
        '<div class="section-heading">📊 Report Overview</div>',
        unsafe_allow_html=True,
    )

    if measurements.empty:
        st.markdown(
            """
            <section class="overview-empty">
                <h3>Make your lab results easier to understand</h3>
                <p>Upload a laboratory report to extract measurements, review
                the results in one place, and compare reports over time.</p>
                <div class="overview-steps">
                    <div class="overview-step">
                        <strong>1. Add a report</strong>
                        <span>Choose a PDF or a clear image of your report.</span>
                    </div>
                    <div class="overview-step">
                        <strong>2. Review results</strong>
                        <span>Check extracted values against the original report.</span>
                    </div>
                    <div class="overview-step">
                        <strong>3. Track changes</strong>
                        <span>Compare results from two report dates.</span>
                    </div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
        return

    total_tests = len(measurements)

    # Identify commonly used result and status columns.
    columns = {
        str(column).strip().lower().replace(" ", "_"): column
        for column in measurements.columns
    }

    status_col = next(
        (
            columns[name]
            for name in ("status", "result_status", "flag")
            if name in columns
        ),
        None,
    )

    value_col = next(
        (
            columns[name]
            for name in ("value", "result", "test_value", "measurement")
            if name in columns
        ),
        None,
    )

    test_col = next(
        (
            columns[name]
            for name in ("test", "test_name", "parameter", "name")
            if name in columns
        ),
        None,
    )

    if status_col:
        status_values = (
            measurements[status_col]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        abnormal_mask = status_values.isin(
            {"low", "high", "abnormal", "out of range", "out-of-range"}
        )

        normal_mask = status_values.isin(
            {"normal", "in range", "within range", "within reference range"}
        )

        abnormal_count = int(abnormal_mask.sum())
        normal_count = int(normal_mask.sum())
        unclassified_count = total_tests - abnormal_count - normal_count

    else:
        abnormal_count = 0
        normal_count = 0
        unclassified_count = total_tests

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Tests", total_tests)
    col2.metric("In Reference Range", normal_count)
    col3.metric("Outside Reference Range", abnormal_count)
    col4.metric("Unclassified", unclassified_count)

    st.caption(
        "Counts are based on extracted status labels. They do not establish "
        "whether a result is medically healthy or unhealthy."
    )

    if status_col:
        chart_data = measurements.copy()
        chart_data["_Dashboard Status"] = (
            chart_data[status_col]
            .fillna("Unknown")
            .astype(str)
        )

        status_chart = (
            chart_data["_Dashboard Status"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Number of Tests")
        )

        st.markdown("#### Test Status Distribution")

        fig = px.pie(
            status_chart,
            names="Status",
            values="Number of Tests",
            hole=0.55,
        )

        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            legend_title_text="Extracted Status",
        )

        st.plotly_chart(fig, use_container_width=True)

    if value_col and test_col:
        numeric_data = measurements.copy()

        numeric_data["_Dashboard Value"] = pd.to_numeric(
            numeric_data[value_col]
            .astype(str)
            .str.replace(",", "", regex=False),
            errors="coerce",
        )

        numeric_data = numeric_data.dropna(
            subset=["_Dashboard Value"]
        )

        if not numeric_data.empty:
            st.markdown("#### Extracted Test Values")

            fig = px.bar(
                numeric_data,
                x=test_col,
                y="_Dashboard Value",
                labels={
                    test_col: "Laboratory Test",
                    "_Dashboard Value": "Extracted Value",
                },
            )

            fig.update_layout(
                margin=dict(t=20, b=20),
                xaxis_title="Laboratory Test",
                yaxis_title="Extracted Value",
            )

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Extracted Measurements")

    st.dataframe(
        measurements,
        use_container_width=True,
        hide_index=True,
    )