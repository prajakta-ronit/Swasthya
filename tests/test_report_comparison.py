import pandas as pd

from src.report_comparison import compare_reports


def test_unit_mismatch_is_reported_without_comparing_values():
    previous = pd.DataFrame({
        "Test": ["Hemoglobin"],
        "Value": ["13.5"],
        "Unit": ["g/dL"],
    })
    current = pd.DataFrame({
        "Test": ["Hemoglobin"],
        "Value": ["14.0"],
        "Unit": ["mmol/L"],
    })

    result = compare_reports(previous, current).iloc[0]

    assert result["Match Status"] == "Unit mismatch — not compared"
    assert not result["Units Compatible"]
    assert pd.isna(result["Change"])
    assert pd.isna(result["Percentage Change (%)"])


def test_compatible_units_still_report_numeric_changes():
    previous = pd.DataFrame({
        "Test": ["Hemoglobin"],
        "Value": ["13.5"],
        "Unit": ["g/dL"],
    })
    current = pd.DataFrame({
        "Test": ["Hemoglobin"],
        "Value": ["14.0"],
        "Unit": ["g/dL"],
    })

    result = compare_reports(previous, current).iloc[0]

    assert result["Match Status"] == "Matched"
    assert result["Units Compatible"]
    assert result["Change"] == 0.5
    assert result["Percentage Change (%)"] == 3.7
