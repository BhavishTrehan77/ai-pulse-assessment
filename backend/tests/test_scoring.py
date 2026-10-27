import json

import pytest

from app.services import llm
from app.services.scoring import score_open_answer


def test_valid_ai_response(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: json.dumps({
            "score": 4,
            "reason": "The answer shows good awareness of AI review practices.",
            "flags": ["unreviewed_output"],
        }),
    )

    result = score_open_answer("test question", "test answer")

    assert result["score"] == 4
    assert result["reason"] == "The answer shows good awareness of AI review practices."
    assert result["flags"] == ["unreviewed_output"]


def test_malformed_ai_response_is_rejected(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: "{not valid json",
    )

    with pytest.raises(ValueError):
        score_open_answer("test question", "test answer")


def test_ai_score_must_be_between_1_and_5(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: json.dumps({
            "score": 7,
            "reason": "Invalid score",
            "flags": [],
        }),
    )

    with pytest.raises(ValueError):
        score_open_answer("test question", "test answer")


def test_ai_score_must_be_an_integer(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: json.dumps({
            "score": "four",
            "reason": "Invalid score",
            "flags": [],
        }),
    )

    with pytest.raises(ValueError):
        score_open_answer("test question", "test answer")


def test_ai_flags_must_be_allowed(monkeypatch):
    monkeypatch.setattr(
        llm,
        "score_answer",
        lambda question, answer: json.dumps({
            "score": 4,
            "reason": "Looks good",
            "flags": ["made_up_flag"],
        }),
    )

    with pytest.raises(ValueError):
        score_open_answer("test question", "test answer")
