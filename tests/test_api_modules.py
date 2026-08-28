"""
NexusTalent Integration API Test Suite
Validates REST API endpoints across HRMS, Recruitment, Attendance, Payroll, Performance, Helpdesk & AI.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_hrms_departments_and_employees(client):
    # List departments
    dept_res = client.get("/api/v1/hrms/departments")
    assert dept_res.status_code == 200
    depts = dept_res.json()
    assert isinstance(depts, list)

    # List employees
    emp_res = client.get("/api/v1/hrms/employees")
    assert emp_res.status_code == 200
    emps = emp_res.json()
    assert len(emps) > 0

    # Org Chart
    org_res = client.get("/api/v1/hrms/org-chart")
    assert org_res.status_code == 200
    org = org_res.json()
    assert len(org) > 0


def test_recruitment_kanban_and_transitions(client):
    req_res = client.get("/api/v1/recruitment/requisitions")
    assert req_res.status_code == 200
    reqs = req_res.json()
    assert len(reqs) > 0
    
    first_req_id = reqs[0]["id"]
    kanban_res = client.get(f"/api/v1/recruitment/kanban/{first_req_id}")
    assert kanban_res.status_code == 200
    columns = kanban_res.json()
    assert len(columns) == 7  # 7 Kanban columns


def test_attendance_dashboard(client):
    res = client.get("/api/v1/attendance/daily-dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_present_today" in data
    assert "records" in data


def test_payroll_runs(client):
    res = client.get("/api/v1/payroll/runs")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)


def test_performance_objectives_and_9box(client):
    obj_res = client.get("/api/v1/performance/objectives")
    assert obj_res.status_code == 200
    
    matrix_res = client.get("/api/v1/performance/nine-box-matrix")
    assert matrix_res.status_code == 200
    assert "matrix" in matrix_res.json()


def test_helpdesk_tickets(client):
    res = client.get("/api/v1/helpdesk/tickets")
    assert res.status_code == 200
    tickets = res.json()
    assert isinstance(tickets, list)


def test_ai_resume_matching_endpoint(client):
    payload = {
        "resume_text": "Experienced in Python, FastAPI, Docker, PostgreSQL, and Kubernetes.",
        "job_description": "We are looking for a Python and FastAPI backend architect with Kubernetes experience.",
        "experience_years": 4.0,
        "min_experience_required": 3.0
    }
    res = client.post("/api/v1/ai/match-resume", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["match_score"] > 75.0
