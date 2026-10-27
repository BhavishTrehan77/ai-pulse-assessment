from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..services.questions import questions_for, load_questions
from ..services.scoring import score_open_answer

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


class AnswerIn(BaseModel):
    question_id: str
    answer: str


class SubmitIn(BaseModel):
    answers: list[AnswerIn]


@router.get("/questions")
def get_questions(m: models.Membership = Depends(current_membership)):
    qs = questions_for(m.job_role, m.seniority)
    # don't leak scoring points to the client
    return [
        {k: v for k, v in q.items() if k != "points"} | (
            {"options": [o["text"] for o in q["options"]]} if q["type"] == "mcq" else {}
        )
        for q in qs
    ]


@router.post("/submit")
def submit(
    body: SubmitIn,
    m: models.Membership = Depends(current_membership),
    db: Session = Depends(get_db),
):
    # Only questions assigned to this employee are valid.
    allowed_questions = questions_for(m.job_role, m.seniority)
    bank = {q["id"]: q for q in allowed_questions}

    # Reject duplicate question IDs before creating any responses.
    seen = set()

    for a in body.answers:
        if a.question_id in seen:
            raise HTTPException(
                400,
                f"Duplicate question {a.question_id}",
            )

        seen.add(a.question_id)

        q = bank.get(a.question_id)

        if not q:
            raise HTTPException(
                400,
                f"Question {a.question_id} is not assigned to this employee",
            )

        if q["type"] == "mcq":
            option = next(
                (o for o in q["options"] if o["text"] == a.answer),
                None,
            )

            if option is None:
                raise HTTPException(
                    400,
                    f"Invalid option for {q['id']}",
                )

    # All structural/authorization validation passed.
    # Now create the responses.
    for a in body.answers:
        q = bank[a.question_id]

        resp = models.Response(
            membership_id=m.id,
            question_id=q["id"],
            answer=a.answer,
        )

        if q["type"] == "mcq":
            option = next(
                o for o in q["options"]
                if o["text"] == a.answer
            )
            resp.score = option["points"]
        else:
            try:
                result = score_open_answer(q["text"], a.answer)
            except ValueError as exc:
                raise HTTPException(
                    502,
                    "AI scoring returned an invalid response",
                ) from exc

            resp.score = result["score"]
            resp.reason = result["reason"]
            resp.flags = result["flags"]

        db.add(resp)

    db.commit()

    return {"saved": len(body.answers)}