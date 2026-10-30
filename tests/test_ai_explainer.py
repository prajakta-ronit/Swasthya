from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

import src.ai_explainer as ai_explainer


def test_explain_measurements_uses_local_ollama_model(monkeypatch):
    chat = Mock(
        return_value=SimpleNamespace(
            message=SimpleNamespace(content="Explanation")
        )
    )
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setattr(
        ai_explainer.ollama,
        "Client",
        lambda **_: SimpleNamespace(chat=chat),
    )

    result = ai_explainer.explain_measurements([{"Test": "Hemoglobin"}])

    assert result == "Explanation"
    assert chat.call_args.kwargs["model"] == "llama3.2:3b"
    assert chat.call_args.kwargs["messages"][1]["content"] == (
        "[{'Test': 'Hemoglobin'}]"
    )
    assert chat.call_args.kwargs["messages"][0]["role"] == "system"


@pytest.mark.parametrize(
    "measurements",
    [
        pd.DataFrame([{"Test": "Hemoglobin", "Value": 13.5}]),
        [{"Test": "Hemoglobin", "Value": 13.5}],
    ],
)
def test_explain_measurements_accepts_dataframe_and_records(
    monkeypatch,
    measurements,
):
    chat = Mock(
        return_value=SimpleNamespace(
            message=SimpleNamespace(content="Explanation")
        )
    )
    monkeypatch.setattr(
        ai_explainer.ollama,
        "Client",
        lambda **_: SimpleNamespace(chat=chat),
    )

    result = ai_explainer.explain_measurements(measurements)

    assert result == "Explanation"
    assert "Hemoglobin" in chat.call_args.kwargs["messages"][1]["content"]


def test_explain_measurements_reports_unavailable_ollama(monkeypatch):
    chat = Mock(side_effect=ai_explainer.ollama.RequestError("connection refused"))
    monkeypatch.setattr(
        ai_explainer.ollama,
        "Client",
        lambda **_: SimpleNamespace(chat=chat),
    )

    with pytest.raises(ai_explainer.OllamaUnavailableError):
        ai_explainer.explain_measurements([{"Test": "Hemoglobin"}])


def test_explain_measurements_reports_missing_model(monkeypatch):
    chat = Mock(
        side_effect=ai_explainer.ollama.ResponseError(
            "model not found",
            status_code=404,
        )
    )
    monkeypatch.setattr(
        ai_explainer.ollama,
        "Client",
        lambda **_: SimpleNamespace(chat=chat),
    )

    with pytest.raises(
        ai_explainer.OllamaModelUnavailableError,
        match="ollama pull llama3.2:3b",
    ):
        ai_explainer.explain_measurements([{"Test": "Hemoglobin"}])
