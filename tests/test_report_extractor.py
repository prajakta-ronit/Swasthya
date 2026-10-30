from src.report_extractor import extract_measurements


def test_extract_measurement_with_reference_range():
    result = extract_measurements(
        "Hemoglobin: 13.5 g/dL\nReference Range: 12.0 - 16.0 g/dL"
    )

    assert list(result.columns) == [
        "Test",
        "Value",
        "Unit",
        "Reference Min",
        "Reference Max",
        "Status",
    ]
    assert result.to_dict("records") == [{
        "Test": "Hemoglobin",
        "Value": "13.5",
        "Unit": "g/dL",
        "Reference Min": 12.0,
        "Reference Max": 16.0,
        "Status": "Within reference range",
    }]


def test_measurement_outside_reference_range_is_flagged():
    result = extract_measurements(
        "Hemoglobin: 10.5 g/dL\nReference Range: 12.0 - 16.0 g/dL"
    )

    assert result.iloc[0]["Status"] == "Below reference range"


def test_measurement_without_reference_range_is_not_interpreted():
    result = extract_measurements("Hemoglobin: 13.5 g/dL")

    assert result.iloc[0]["Reference Min"] is None
    assert result.iloc[0]["Reference Max"] is None
    assert result.iloc[0]["Status"] == "Reference range unavailable"


def test_unrecognized_text_returns_empty_result_with_expected_columns():
    result = extract_measurements("No supported lab results found.")

    assert result.empty
    assert list(result.columns) == [
        "Test",
        "Value",
        "Unit",
        "Reference Min",
        "Reference Max",
        "Status",
    ]
