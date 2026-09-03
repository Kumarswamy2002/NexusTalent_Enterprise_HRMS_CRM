"""
NexusTalent CRM Enhancements Test Suite
Validates Candidate Talent Pool Directory, Search & Filtering, Interaction Notes Timeline,
Candidate Rich Profile, and Pipeline Funnel Analytics.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_crm_candidate_talent_pool_listing(client):
    # 1. Fetch all candidates
    res = client.get("/api/v1/recruitment/candidates")
    assert res.status_code == 200
    candidates = res.json()
    assert isinstance(candidates, list)
    assert len(candidates) >= 5

    # Verify attributes
    c0 = candidates[0]
    assert "full_name" in c0
    assert "email" in c0
    assert "source" in c0
    assert "skills_tags" in c0
    assert "application_count" in c0
    assert "notes_count" in c0

    # 2. Search filtering
    search_res = client.get("/api/v1/recruitment/candidates?search=Python")
    assert search_res.status_code == 200
    matched_cands = search_res.json()
    assert len(matched_cands) > 0
    for cand in matched_cands:
        text = f"{cand['full_name']} {cand['skills_tags']} {cand['current_company']} {cand['current_title']}"
        assert "python" in text.lower()

    # 3. Source filtering
    source_res = client.get("/api/v1/recruitment/candidates?source=linkedin")
    assert source_res.status_code == 200
    linkedin_cands = source_res.json()
    assert len(linkedin_cands) > 0
    for cand in linkedin_cands:
        assert cand["source"] == "linkedin"

    # 4. Minimum experience filtering
    exp_res = client.get("/api/v1/recruitment/candidates?min_experience=5.0")
    assert exp_res.status_code == 200
    senior_cands = exp_res.json()
    assert len(senior_cands) > 0
    for cand in senior_cands:
        assert cand["years_of_experience"] >= 5.0


def test_crm_candidate_detail(client):
    # Get any candidate ID
    list_res = client.get("/api/v1/recruitment/candidates")
    cand_id = list_res.json()[0]["id"]

    # Fetch detail
    detail_res = client.get(f"/api/v1/recruitment/candidates/{cand_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == cand_id
    assert "applications" in detail
    assert "notes" in detail
    assert isinstance(detail["applications"], list)


def test_crm_candidate_notes_timeline(client):
    list_res = client.get("/api/v1/recruitment/candidates")
    cand_id = list_res.json()[0]["id"]

    # Post note
    payload = {
        "note_type": "screening",
        "content": "Conducted initial recruiter screen: candidate confirmed interest, target compensation $185k base, available in 3 weeks."
    }
    post_res = client.post(f"/api/v1/recruitment/candidates/{cand_id}/notes", json=payload)
    assert post_res.status_code == 201
    created_note = post_res.json()
    assert created_note["note_type"] == "screening"
    assert created_note["content"] == payload["content"]
    assert created_note["author_name"] == "Recruiter Admin"

    # Fetch notes timeline
    get_res = client.get(f"/api/v1/recruitment/candidates/{cand_id}/notes")
    assert get_res.status_code == 200
    notes = get_res.json()
    assert len(notes) >= 1
    assert notes[0]["content"] == payload["content"]


def test_crm_pipeline_funnel_analytics(client):
    res = client.get("/api/v1/recruitment/analytics/pipeline-summary")
    assert res.status_code == 200
    data = res.json()

    assert "total_candidates" in data
    assert "total_applications" in data
    assert "stage_breakdown" in data
    assert "source_attribution" in data
    assert "conversion_rates" in data
    assert "avg_ai_match_score" in data

    assert data["total_candidates"] >= 5
    assert "applied" in data["stage_breakdown"]
    assert "interviewing" in data["stage_breakdown"]
    assert "hired" in data["stage_breakdown"]
    assert "interview_rate" in data["conversion_rates"]
