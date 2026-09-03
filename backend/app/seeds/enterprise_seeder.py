"""
NexusTalent Enterprise Mock Seeder
Generates full-scale enterprise data across HRMS, Recruitment CRM, Attendance, Payroll, Performance & Helpdesk.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.config import settings
from backend.app.modules.hrms.models import Department, Designation, Employee, EmploymentType, EmployeeStatus
from backend.app.modules.recruitment.models import (
    JobRequisition, Candidate, CandidateApplication, InterviewScorecard,
    RequisitionStatus, CandidateSource, PipelineStage
)
from backend.app.modules.attendance.models import (
    AttendanceRecord, AttendanceType, LeaveRequest, LeaveType, LeaveStatus
)
from backend.app.modules.payroll.models import SalaryStructure, PayrollRun, Payslip, PayrollRunStatus
from backend.app.modules.performance.models import Objective, KeyResult, NineBoxAssessment, OKRLevel, GoalStatus
from backend.app.modules.performance.nine_box_engine import NineBoxEngine
import logging
from backend.app.modules.helpdesk.models import HelpdeskTicket, TicketCategory, TicketPriority, TicketStatus, TicketComment

logger = logging.getLogger("EnterpriseSeeder")


async def seed_enterprise_data(session: AsyncSession):
    tenant = settings.DEFAULT_TENANT_ID

    # Check if already seeded
    check = await session.execute(select(func.count(Employee.id)).where(Employee.tenant_id == tenant))
    if (check.scalar() or 0) > 0:
        return

    logger.info("Seeding Enterprise NexusTalent Data...")

    # 1. Create Departments
    dept_eng = Department(id="dept_eng", tenant_id=tenant, name="Engineering & AI", code="ENG", budget=2500000.0, location="San Francisco HQ")
    dept_prod = Department(id="dept_prod", tenant_id=tenant, name="Product & Design", code="PROD", budget=1200000.0, location="San Francisco HQ")
    dept_people = Department(id="dept_people", tenant_id=tenant, name="People Operations & Talent", code="PEOP", budget=600000.0, location="New York Office")
    dept_sales = Department(id="dept_sales", tenant_id=tenant, name="Sales & Growth", code="SALES", budget=1800000.0, location="London Hub")
    dept_exec = Department(id="dept_exec", tenant_id=tenant, name="Executive Leadership", code="EXEC", budget=3000000.0, location="San Francisco HQ")

    session.add_all([dept_eng, dept_prod, dept_people, dept_sales, dept_exec])
    await session.flush()

    # 2. Create Employees & Org Hierarchy
    # Level 1: CEO
    emp_ceo = Employee(
        id="emp_001_ceo",
        tenant_id=tenant,
        employee_code="NX-1001",
        first_name="Alexander",
        last_name="Vance",
        email="alexander.vance@nexustalent.enterprise",
        phone="+1 415 555 0101",
        department_id=dept_exec.id,
        designation="Chief Executive Officer",
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2022, 1, 15),
        work_location="San Francisco HQ",
        is_remote=False,
        base_annual_salary=320000.0
    )

    # Level 2: VP Engineering & Head of People
    emp_vpeng = Employee(
        id="emp_002_vpeng",
        tenant_id=tenant,
        employee_code="NX-1002",
        first_name="Elena",
        last_name="Rostova",
        email="elena.rostova@nexustalent.enterprise",
        phone="+1 415 555 0102",
        department_id=dept_eng.id,
        designation="VP of Engineering",
        manager_id=emp_ceo.id,
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2022, 3, 1),
        work_location="San Francisco HQ",
        is_remote=False,
        base_annual_salary=240000.0
    )

    emp_hrhead = Employee(
        id="emp_003_hrhead",
        tenant_id=tenant,
        employee_code="NX-1003",
        first_name="Marcus",
        last_name="Chen",
        email="marcus.chen@nexustalent.enterprise",
        phone="+1 415 555 0103",
        department_id=dept_people.id,
        designation="Head of People & Culture",
        manager_id=emp_ceo.id,
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2022, 4, 10),
        work_location="New York Office",
        is_remote=False,
        base_annual_salary=195000.0
    )

    # Level 3: Leads, Engineers & Recruiters
    emp_staff = Employee(
        id="emp_004_staff",
        tenant_id=tenant,
        employee_code="NX-1004",
        first_name="Sophia",
        last_name="Sterling",
        email="sophia.sterling@nexustalent.enterprise",
        phone="+1 415 555 0104",
        department_id=dept_eng.id,
        designation="Staff Engineer",
        manager_id=emp_vpeng.id,
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2023, 2, 1),
        work_location="San Francisco HQ",
        is_remote=True,
        base_annual_salary=185000.0
    )

    emp_srdev = Employee(
        id="emp_005_srdev",
        tenant_id=tenant,
        employee_code="NX-1005",
        first_name="Devon",
        last_name="Miles",
        email="devon.miles@nexustalent.enterprise",
        phone="+1 415 555 0105",
        department_id=dept_eng.id,
        designation="Senior Software Engineer",
        manager_id=emp_staff.id,
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2023, 6, 15),
        work_location="San Francisco HQ",
        is_remote=False,
        base_annual_salary=145000.0
    )

    emp_recruiter = Employee(
        id="emp_006_recruiter",
        tenant_id=tenant,
        employee_code="NX-1006",
        first_name="Rachel",
        last_name="Kim",
        email="rachel.kim@nexustalent.enterprise",
        phone="+1 415 555 0106",
        department_id=dept_people.id,
        designation="Senior Talent Lead",
        manager_id=emp_hrhead.id,
        employment_type=EmploymentType.FULL_TIME,
        status=EmployeeStatus.ACTIVE,
        date_of_joining=date(2023, 8, 1),
        work_location="New York Office",
        is_remote=True,
        base_annual_salary=115000.0
    )

    session.add_all([emp_ceo, emp_vpeng, emp_hrhead, emp_staff, emp_srdev, emp_recruiter])
    await session.flush()

    # 3. Create Job Requisitions
    req1 = JobRequisition(
        id="req_001_backend",
        tenant_id=tenant,
        code="REQ-2001",
        title="Staff Distributed Backend Engineer",
        department_id=dept_eng.id,
        hiring_manager_id=emp_vpeng.id,
        open_positions=2,
        status=RequisitionStatus.OPEN,
        location="San Francisco / Remote",
        experience_years_min=5,
        min_budget=160000.0,
        max_budget=210000.0,
        currency="USD",
        job_description="Architecting high-throughput microservices in Python/FastAPI and Go with Kafka event pipelines.",
        required_skills="Python, FastAPI, Kafka, Docker, Kubernetes, PostgreSQL, Distributed Systems"
    )

    req2 = JobRequisition(
        id="req_002_pm",
        tenant_id=tenant,
        code="REQ-2002",
        title="Lead Product Manager - AI Talent Tools",
        department_id=dept_prod.id,
        hiring_manager_id=emp_ceo.id,
        open_positions=1,
        status=RequisitionStatus.OPEN,
        location="San Francisco HQ",
        experience_years_min=4,
        min_budget=140000.0,
        max_budget=185000.0,
        currency="USD",
        job_description="Leading product vision and roadmap for autonomous recruitment CRM and AI matching platforms.",
        required_skills="Product Management, Agile, Machine Learning, UI/UX, B2B SaaS"
    )

    session.add_all([req1, req2])
    await session.flush()

    # 4. Create Candidates & Applications across Kanban Stages
    cand_data = [
        ("Liam", "Nakamura", "liam.nakamura@example.com", "Senior Backend Engineer", "Stripe", 6.5, "Python, FastAPI, Kubernetes, Kafka, PostgreSQL", CandidateSource.LINKEDIN, PipelineStage.TECH_ASSESSMENT, 94.0),
        ("Aria", "Montgomery", "aria.m@example.com", "Principal Architect", "Datadog", 8.0, "Python, Go, Distributed Systems, Kafka, AWS", CandidateSource.DIRECT_OUTREACH, PipelineStage.OFFER_EXTENDED, 98.0),
        ("Kavita", "Patel", "kavita.patel@example.com", "Software Engineer II", "Uber", 4.0, "Python, Django, PostgreSQL, Docker", CandidateSource.REFERRAL, PipelineStage.INTERVIEWING, 86.0),
        ("Ethan", "Hawthorne", "ethan.h@example.com", "Full Stack Developer", "Airbnb", 3.5, "TypeScript, React, Python, FastAPI", CandidateSource.CAREER_PORTAL, PipelineStage.SCREENING, 82.0),
        ("Maya", "Lin", "maya.lin@example.com", "Product Manager", "Figma", 5.0, "Product Management, Agile, SaaS, ML", CandidateSource.LINKEDIN, PipelineStage.APPLIED, 91.0),
        ("Lucas", "Alvarez", "lucas.a@example.com", "DevOps Engineer", "Cloudflare", 5.5, "Kubernetes, Terraform, AWS, Python", CandidateSource.CAREER_PORTAL, PipelineStage.HIRED, 95.0),
    ]

    for f_name, l_name, email, title, comp, exp, skills, source, stage, score in cand_data:
        cand = Candidate(
            id=str(uuid.uuid4()),
            tenant_id=tenant,
            first_name=f_name,
            last_name=l_name,
            email=email,
            current_company=comp,
            current_title=title,
            years_of_experience=exp,
            skills_tags=skills,
            source=source,
            ai_match_score=score
        )
        session.add(cand)
        await session.flush()

        app = CandidateApplication(
            id=str(uuid.uuid4()),
            tenant_id=tenant,
            candidate_id=cand.id,
            requisition_id=req1.id if "Engineer" in title or "Architect" in title or "DevOps" in title else req2.id,
            stage=stage,
            overall_rating=4.5 if score > 90 else 3.8
        )
        session.add(app)
        await session.flush()

        # Add scorecard for interviewing/tech stage
        if stage in (PipelineStage.INTERVIEWING, PipelineStage.TECH_ASSESSMENT, PipelineStage.OFFER_EXTENDED, PipelineStage.HIRED):
            scorecard = InterviewScorecard(
                id=str(uuid.uuid4()),
                tenant_id=tenant,
                application_id=app.id,
                interviewer_id=emp_vpeng.id,
                round_name="Architecture & Systems",
                technical_score=5 if score > 90 else 4,
                communication_score=4,
                cultural_fit_score=5,
                recommendation="strong_yes",
                feedback_notes=f"Outstanding command of distributed systems, concurrency, and clean code principles."
            )
            session.add(scorecard)

    # 5. Create Attendance Records for Today
    today = date.today()
    for emp in [emp_ceo, emp_vpeng, emp_hrhead, emp_staff, emp_srdev]:
        att = AttendanceRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant,
            employee_id=emp.id,
            work_date=today,
            clock_in=datetime.now(timezone.utc).replace(hour=8, minute=55, second=0),
            attendance_type=AttendanceType.REMOTE if emp.is_remote else AttendanceType.OFFICE,
            latitude_in=settings.HQ_LATITUDE,
            longitude_in=settings.HQ_LONGITUDE,
            distance_from_hq_meters=15.0,
            is_geofence_verified=True,
            is_late=False
        )
        session.add(att)

    # 6. Create Leave Requests
    leave1 = LeaveRequest(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        employee_id=emp_srdev.id,
        leave_type=LeaveType.PAID_TIME_OFF,
        start_date=today + timedelta(days=5),
        end_date=today + timedelta(days=7),
        total_days=3.0,
        reason="Family vacation and personal travel.",
        status=LeaveStatus.SUBMITTED
    )
    session.add(leave1)

    # 7. Create Salary Structure & Payroll Run
    sal_struct = SalaryStructure(
        id="struct_standard_us",
        tenant_id=tenant,
        name="US Standard Tech Compensation Matrix",
        currency="USD",
        basic_percentage=50.0,
        hra_percentage=20.0,
        special_allowance_formula="CTC - (BASIC + HRA)",
        pf_deduction_rate=5.0,
        tax_rate_estimated=18.0
    )
    session.add(sal_struct)
    await session.flush()

    payroll_run = PayrollRun(
        id="run_current_month",
        tenant_id=tenant,
        period_month=today.month,
        period_year=today.year,
        status=PayrollRunStatus.CALCULATED,
        total_gross_disbursed=100416.67,
        total_deductions=23095.83,
        total_net_disbursed=77320.84,
        total_employees_processed=6
    )
    session.add(payroll_run)
    await session.flush()

    # 8. Create Objectives & Key Results (OKRs)
    obj1 = Objective(
        id="obj_q1_ai_infra",
        tenant_id=tenant,
        title="Deliver Sub-10ms Microservices Architecture for Enterprise HRMS",
        level=OKRLevel.DEPARTMENT,
        owner_id=emp_vpeng.id,
        quarter="Q1-2026",
        progress_percentage=75.0,
        status=GoalStatus.ON_TRACK
    )
    session.add(obj1)
    await session.flush()

    kr1 = KeyResult(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        objective_id=obj1.id,
        title="Complete Universal State Machine & ABAC Security Policy Engine",
        target_value=100.0,
        current_value=100.0,
        metric_unit="%"
    )
    kr2 = KeyResult(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        objective_id=obj1.id,
        title="Achieve 99.99% Attendance & Geofence calculation accuracy",
        target_value=100.0,
        current_value=75.0,
        metric_unit="%"
    )
    session.add_all([kr1, kr2])

    # 9. Create 9-Box Calibration Ratings
    box1 = NineBoxAssessment(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        employee_id=emp_staff.id,
        reviewer_id=emp_vpeng.id,
        performance_score=3,
        potential_score=3,
        box_category="Star / Future Leader",
        notes="Consistently drives cross-functional technical architecture with exemplary domain modeling."
    )
    box2 = NineBoxAssessment(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        employee_id=emp_srdev.id,
        reviewer_id=emp_vpeng.id,
        performance_score=3,
        potential_score=2,
        box_category="High Performer",
        notes="Exceptional delivery speed, expanding mentorship towards junior engineers."
    )
    session.add_all([box1, box2])

    # 10. Create Helpdesk Tickets
    ticket1 = HelpdeskTicket(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        ticket_number="TICK-3001",
        employee_id=emp_srdev.id,
        category=TicketCategory.BENEFITS_INSURANCE,
        priority=TicketPriority.MEDIUM,
        subject="Enrollment inquiry for International Health Plan addition",
        description="I would like to upgrade my health coverage policy to include international dependents coverage.",
        status=TicketStatus.IN_PROGRESS,
        assigned_to_id=emp_hrhead.id
    )
    session.add(ticket1)
    await session.flush()

    comment1 = TicketComment(
        id=str(uuid.uuid4()),
        tenant_id=tenant,
        ticket_id=ticket1.id,
        author_id=emp_hrhead.id,
        author_name=emp_hrhead.full_name,
        message="Hi Devon, the international rider paperwork has been queued. Please verify your current address proof."
    )
    session.add(comment1)

    await session.commit()
    logger.info("NexusTalent Enterprise Data Successfully Seeded!")
