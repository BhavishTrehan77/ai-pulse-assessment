from tests.conftest import login
from app import models
from app.auth import hash_password
from app.db import SessionLocal


def test_login_lists_organizations(client):
    _, data = login(client, "ravi@consult.test")
    names = {o["org_name"] for o in data["organizations"]}
    assert names == {"Northwind Logistics", "Bluepeak Retail"}


def test_employee_sees_questions(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/diagnostic/questions", headers=headers)
    assert r.status_code == 200
    assert any(q["id"] == "sup-drafts" for q in r.json())



def test_admin_cannot_see_other_org(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")

    r = client.get("/dashboard?org_id=2", headers=headers)

    assert r.status_code == 403
    assert r.json()["detail"] == "Not a member of this organization"


def test_admin_dashboard(client):
    headers, data = login(client, "asha@northwind.test", "Northwind Logistics")
    org_id = data["organizations"][0]["org_id"]

    r = client.get(f"/dashboard?org_id={org_id}", headers=headers)

    assert r.status_code == 200
    assert "departments" in r.json()

def test_small_departments_are_hidden(client):
    headers, data = login(client, "asha@northwind.test", "Northwind Logistics")
    org_id = data["organizations"][0]["org_id"]

    r = client.get(f"/dashboard?org_id={org_id}", headers=headers)

    assert r.status_code == 200

    body = r.json()

    # Seeded Northwind departments currently have fewer than
    # 5 completed/responded employees.
    assert body["departments"] == []

    # The only seeded risk comes from a small department,
    # so it must not leak through the organization-level risk summary.
    assert body["top_risks"] == []

def test_large_department_is_visible(client):
    db = SessionLocal()

    try:
        org = db.query(models.Organization).filter_by(
            name="Northwind Logistics"
        ).one()

        sales = next(
            dept for dept in org.departments
            if dept.name == "Sales"
        )

        # Seed data already has Vikram with responses in Sales.
        # Add four more respondents so Sales reaches 5 completed diagnostics.
        for i in range(4):
            user = models.User(
                name=f"Privacy Test {i}",
                email=f"privacy-test-{i}@example.test",
                password_hash=hash_password("pulse123"),
            )
            db.add(user)
            db.flush()

            membership = models.Membership(
                user_id=user.id,
                org_id=org.id,
                department_id=sales.id,
                role="employee",
                job_role="sales",
                seniority="mid",
            )
            db.add(membership)
            db.flush()

            db.add(
                models.Response(
                    membership_id=membership.id,
                    question_id=f"privacy-test-{i}",
                    answer="test",
                    score=3,
                    flags=["test_risk"],
                )
            )

        db.commit()
    finally:
        db.close()

    headers, data = login(
        client,
        "asha@northwind.test",
        "Northwind Logistics",
    )

    org_id = data["organizations"][0]["org_id"]

    r = client.get(
        f"/dashboard?org_id={org_id}",
        headers=headers,
    )

    assert r.status_code == 200

    body = r.json()

    sales_data = next(
        dept for dept in body["departments"]
        if dept["department"] == "Sales"
    )

    assert sales_data["responded"] == 5
    assert sales_data["average_score"] == 3.33
    assert ["test_risk", 4] in body["top_risks"]