from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..utils import maturity_level

router = APIRouter(prefix="/reports", tags=["reports"])


NEXT_STEPS = {
    "support": [
        "Use AI to draft first replies, then edit",
        "Summarise long ticket threads before escalating",
        "Never paste customer details into public chatbots",
    ],
    "engineering": [
        "Use a code assistant for tests and refactors",
        "Review every AI suggestion before merging",
        "Keep secrets and customer data out of prompts",
    ],
    "sales": [
        "Draft outreach emails with AI and personalise them",
        "Summarise call notes into CRM updates",
        "Check AI-written claims before sending",
    ],
    "manager": [
        "Agree an AI usage policy with your team",
        "Pick one workflow per quarter to improve with AI",
        "Track time saved, not tool licences",
    ],
}


RISK_ACTIONS = {
    "customer_data_shared": {
        "title": "Protect customer data",
        "action": (
            "Remove customer-identifying information before using AI "
            "and only use approved AI tools for customer-related work."
        ),
    },
    "confidential_data_shared": {
        "title": "Protect confidential information",
        "action": (
            "Do not paste confidential documents, credentials, or "
            "proprietary information into unapproved AI tools."
        ),
    },
    "unreviewed_output": {
        "title": "Review AI output before using it",
        "action": (
            "Treat AI output as a draft and verify facts, logic, "
            "and policy compliance before sending or merging it."
        ),
    },
    "policy_unaware": {
        "title": "Review AI usage policy",
        "action": (
            "Review your organization's approved AI tools and "
            "data-handling rules before using AI for work."
        ),
    },
}


def build_action_plan(flags: list[str]) -> list[dict[str, str]]:
    action_plan = []

    for flag in flags:
        recommendation = RISK_ACTIONS.get(flag)

        if recommendation:
            action_plan.append(
                {
                    "risk": flag,
                    "title": recommendation["title"],
                    "action": recommendation["action"],
                }
            )

    return action_plan


@router.get("/me")
def my_report(
    m: models.Membership = Depends(current_membership),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Response)
        .filter_by(membership_id=m.id)
        .all()
    )

    scores = [
        r.score
        for r in rows
        if r.score is not None
    ]

    avg = sum(scores) / len(scores) if scores else None

    flags = sorted(
        {
            f
            for r in rows
            for f in (r.flags or [])
        }
    )

    return {
        "name": m.user.name,
        "organization": m.org.name,
        "answered": len(rows),
        "average_score": round(avg, 2) if avg is not None else None,
        "level": maturity_level(avg),
        "risks": flags,
        "next_steps": NEXT_STEPS.get(
            m.job_role,
            NEXT_STEPS["manager"],
        ),
        "action_plan": build_action_plan(flags),
    }


@router.delete("/me")
def delete_my_diagnostic(
    m: models.Membership = Depends(current_membership),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(models.Response)
        .filter_by(membership_id=m.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "deleted": deleted,
    }