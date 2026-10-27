import json

from . import llm


ALLOWED_FLAGS = {
    "customer_data_shared",
    "confidential_data_shared",
    "unreviewed_output",
    "policy_unaware",
}


def score_open_answer(question_text: str, answer: str) -> dict:
    raw = llm.score_answer(question_text, answer)

    # Some models wrap otherwise-valid JSON in a markdown code block.
    cleaned = raw.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("AI returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")

    score = data.get("score")

    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("AI score must be an integer")

    if not 1 <= score <= 5:
        raise ValueError("AI score must be between 1 and 5")

    reason = data.get("reason")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("AI reason must be a non-empty string")

    flags = data.get("flags", [])

    if not isinstance(flags, list):
        raise ValueError("AI flags must be a list")

    invalid_flags = set(flags) - ALLOWED_FLAGS

    if invalid_flags:
        raise ValueError(
            f"AI returned unknown flags: {sorted(invalid_flags)}"
        )

    if any(not isinstance(flag, str) for flag in flags):
        raise ValueError("AI flags must contain only strings")

    return {
        "score": score,
        "reason": reason.strip(),
        "flags": flags,
    }