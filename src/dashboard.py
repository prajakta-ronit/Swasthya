import pandas as pd
import streamlit as st
import plotly.express as px


def apply_dashboard_style():
    """Apply a professional visual theme to SWASTHYA AI."""

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f5f8fc;
        }

        [data-testid="stSidebar"] {
            background-color: #eaf2fb;
            border-right: 1px solid #d8e4f0;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        .dashboard-title {
            font-size: 2.35rem;
            font-weight: 750;
            color: #153e66;
            margin-bottom: 0.2rem;
        }

        .dashboard-subtitle {
            color: #61758a;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .section-heading {
            color: #153e66;
            font-size: 1.35rem;
            font-weight: 650;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        div[data-testid="stMetric"] {
            background-color: white;
            border: 1px solid #dce7f2;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(21, 62, 102, 0.05);
        }

        div[data-testid="stMetricLabel"] {
            color: #61758a;
        }

        div[data-testid="stMetricValue"] {
            color: #153e66;
        }

        div[data-testid="stAlert"] {
            border-radius: 10px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def show_dashboard_header():
    """Display the dashboard heading."""

    st.markdown(
        '<div class="dashboard-title">🩺 SWASTHYA AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'AI-Powered Medical Report Analysis & Health Insights'
        '</div>',
        unsafe_allow_html=True,
    )


def show_overview(measurements: pd.DataFrame):
    """Display summary metrics and charts for extracted results."""

    st.markdown(
        '<div class="section-heading">📊 Report Overview</div>',
        unsafe_allow_html=True,
    )

    if measurements.empty:
        st.info(
            "Upload a medical report to view your dashboard statistics."
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