from backend.app.services.onboarding_orchestrator_service import OnboardingOrchestrator

def test_onboarding_initialization():
    plan = OnboardingOrchestrator.initialize_onboarding_plan("emp-999", "Backend Engineer")
    assert plan["total_tasks"] == 4
    assert plan["progress_percent"] == 0.0
