import re

import pandas as pd


TEST_PATTERNS = {
    "Hemoglobin": r"hemoglobin|haemoglobin|hgb",
    "WBC Count": r"wbc count|white blood cell count|total leukocyte count",
    "RBC Count": r"rbc count|red blood cell count",
    "Platelet Count": r"platelet count|platelets",
    "Glucose": r"blood glucose|glucose",
    "Vitamin D": r"vitamin d",
    "Creatinine": r"creatinine",
}

RANGE_PATTERN = re.compile(
    r"(?:reference\s*range|normal\s*range|ref\.?\s*range)"
    r"\s*[:\-]?\s*"
    r"(\d[\d,]*(?:\.\d+)?)\s*[-–—]\s*"
    r"(\d[\d,]*(?:\.\d+)?)",
    re.IGNORECASE,
)

NUMBER_RANGE_PATTERN = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*[-–—]\s*"
    r"(\d[\d,]*(?:\.\d+)?)"
)


def extract_measurements(text: str) -> pd.DataFrame:
    """Extract supported measurements and any nearby reference ranges."""
    lines = text.splitlines()
    records = []

    for index, line in enumerate(lines):
        for test_name, pattern in TEST_PATTERNS.items():
            match = re.search(
                rf"\b(?:{pattern})\b\s*[:\-]?\s*"
                r"([<>]?\s*\d[\d,]*(?:\.\d+)?)"
                r"\s*([a-zA-Z/%³μµ]+(?:\s*/\s*[a-zA-Z0-9³μµ]+)*)?",
                line,
                re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1).replace(" ", "")
            unit = (match.group(2) or "").strip()
            reference_min = None
            reference_max = None

            for candidate in lines[index:index + 6]:
                range_match = RANGE_PATTERN.search(candidate)
                if not range_match and re.search(
                    r"reference|normal|range|ref\.?",
                    candidate,
                    re.IGNORECASE,
                ):
                    range_match = NUMBER_RANGE_PATTERN.search(candidate)

                if range_match:
                    reference_min = float(
                        range_match.group(1).replace(",", "")
                    )
                    reference_max = float(
                        range_match.group(2).replace(",", "")
                    )
                    break

            if reference_min is None:
                status = "Reference range unavailable"
            elif value.startswith(("<", ">")):
                status = "Requires interpretation"
            else:
                numeric_value = float(value.replace(",", ""))
                if numeric_value < reference_min:
                    status = "Below reference range"
                elif numeric_value > reference_max:
                    status = "Above reference range"
                else:
                    status = "Within reference range"

            records.append({
                "Test": test_name,
                "Value": value,
                "Unit": unit,
                "Reference Min": reference_min,
                "Reference Max": reference_max,
                "Status": status,
            })
            break

    return pd.DataFrame(
        records,
        columns=[
            "Test",
            "Value",
            "Unit",
            "Reference Min",
            "Reference Max",
            "Status",
        ],
    )
