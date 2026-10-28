from app.routes.reports import build_action_plan


def test_action_plan_maps_known_risks():
    result = build_action_plan(
        [
            "customer_data_shared",
            "unreviewed_output",
        ]
    )

    assert result == [
        {
            "risk": "customer_data_shared",
            "title": "Protect customer data",
            "action": (
                "Remove customer-identifying information before using AI "
                "and only use approved AI tools for customer-related work."
            ),
        },
        {
            "risk": "unreviewed_output",
            "title": "Review AI output before using it",
            "action": (
                "Treat AI output as a draft and verify facts, logic, "
                "and policy compliance before sending or merging it."
            ),
        },
    ]


def test_action_plan_ignores_unknown_risks():
    result = build_action_plan(
        [
            "unknown_risk",
            "policy_unaware",
        ]
    )

    assert len(result) == 1
    assert result[0]["risk"] == "policy_unaware"


def test_action_plan_is_empty_without_known_risks():
    assert build_action_plan([]) == []