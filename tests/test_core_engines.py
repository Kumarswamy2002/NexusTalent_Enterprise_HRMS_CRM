"""
NexusTalent Enterprise Engine Unit Tests
Validates Universal State Machine, AST Safe Formula Parser, Geofencing, Dynamic Schema & ABAC Policies.
"""

import pytest
from backend.app.core.workflow_engine import WORKFLOW_REGISTRY, TransitionError
from backend.app.core.dynamic_fields import DynamicFieldEngine, CustomFieldDefinition, FieldType
from backend.app.core.security import PolicyEngine, UserContext
from backend.app.modules.payroll.formula_evaluator import SafeFormulaEvaluator, FormulaEvaluationError
from backend.app.modules.attendance.geofence_engine import GeofenceEngine
from backend.app.modules.performance.nine_box_engine import NineBoxEngine
from backend.app.modules.ai_engine.resume_parser import SkillMatcher
from backend.app.modules.ai_engine.attrition_predictor import attrition_ai_model


def test_workflow_leave_transitions():
    wf = WORKFLOW_REGISTRY["leave_request"]
    
    # Valid transition: draft -> submitted by employee
    assert wf.can_transition("draft", "submitted", {"employee"}) is True
    
    # Manager approval: submitted -> manager_approved
    assert wf.can_transition("submitted", "manager_approved", {"hiring_manager"}) is True
    
    # Illegal direct leap: draft -> approved should fail
    assert wf.can_transition("draft", "approved", {"employee"}) is False


def test_workflow_recruitment_pipeline():
    wf = WORKFLOW_REGISTRY["recruitment_pipeline"]
    
    assert wf.can_transition("applied", "screening", {"recruiter"}) is True
    assert wf.can_transition("screening", "interviewing", {"recruiter"}) is True
    assert wf.can_transition("offer_extended", "hired", {"hr_admin"}) is False  # Must accept first
    assert wf.can_transition("offer_accepted", "hired", {"hr_admin"}) is True


def test_ast_safe_formula_evaluator():
    variables = {"CTC": 120000.0, "BASIC": 60000.0, "HRA": 24000.0, "BONUS": 5000.0}
    
    # Valid formula
    res = SafeFormulaEvaluator.evaluate("CTC - (BASIC + HRA) + BONUS", variables)
    assert res == 41000.0

    # Arithmetic precedence
    res2 = SafeFormulaEvaluator.evaluate("BASIC * 0.5 + 1000", variables)
    assert res2 == 31000.0

    # Unsafe operation rejection
    with pytest.raises(FormulaEvaluationError):
        SafeFormulaEvaluator.evaluate("__import__('os').system('ls')", variables)


def test_geofence_distance_calculation():
    # San Francisco coordinates
    lat1, lon1 = 37.7749, -122.4194
    # 50 meters away
    lat2, lon2 = 37.7752, -122.4194
    
    is_valid, dist = GeofenceEngine.verify_location(lat2, lon2, lat1, lon1, max_allowed_meters=200.0)
    assert is_valid is True
    assert dist < 200.0

    # Far away (e.g. Los Angeles)
    lat_la, lon_la = 34.0522, -118.2437
    is_valid_far, dist_far = GeofenceEngine.verify_location(lat_la, lon_la, lat1, lon1, max_allowed_meters=200.0)
    assert is_valid_far is False
    assert dist_far > 100000.0


def test_dynamic_fields_validation():
    defs = [
        CustomFieldDefinition(name="visa_type", label="Visa Status", field_type=FieldType.SELECT, options=["H1B", "Citizen", "L1"]),
        CustomFieldDefinition(name="github_handle", label="GitHub", field_type=FieldType.STRING, is_required=True),
        CustomFieldDefinition(name="years_experience", label="Years Exp", field_type=FieldType.NUMBER, default_value=0.0)
    ]
    
    valid_data = {"visa_type": "H1B", "github_handle": "torvalds", "years_experience": "12.5"}
    cleaned = DynamicFieldEngine.validate_and_sanitize(defs, valid_data)
    assert cleaned["visa_type"] == "H1B"
    assert cleaned["years_experience"] == 12.5

    # Missing required field
    with pytest.raises(ValueError):
        DynamicFieldEngine.validate_and_sanitize(defs, {"visa_type": "H1B"})


def test_nine_box_classification():
    top = NineBoxEngine.classify(3, 3)
    assert "Star" in top["category"]

    risk = NineBoxEngine.classify(1, 1)
    assert "Risk" in risk["category"]


def test_ai_resume_matcher():
    text = "Senior Software Engineer with 6 years experience in Python, FastAPI, Docker, and PostgreSQL."
    skills = SkillMatcher.extract_skills_from_text(text)
    assert "Python" in skills
    assert "Fastapi" in skills or "FastAPI" in skills

    match = SkillMatcher.calculate_match_score(
        candidate_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        required_skills=["Python", "FastAPI", "Kafka", "PostgreSQL"],
        experience_years=5.0,
        min_experience_required=3.0
    )
    assert match["match_score"] > 80.0


def test_ai_attrition_prediction():
    res = attrition_ai_model.predict_employee_risk(
        salary_ratio=0.8,
        overtime_hours_month=35.0,
        tenure_years=3.0,
        years_since_last_promotion=3.5,
        performance_score=2.0,
        is_remote=False
    )
    assert "flight_risk_percentage" in res
    assert res["flight_risk_percentage"] > 40.0
