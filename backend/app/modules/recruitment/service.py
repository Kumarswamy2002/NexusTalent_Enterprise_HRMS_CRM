"""
NexusTalent Recruitment Pipeline Engine & Service
Handles Candidate Sourcing, Kanban State Progression, Scoring & Automatic Offer Transition.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from backend.app.modules.recruitment.models import (
    JobRequisition, Candidate, CandidateApplication, InterviewScorecard, CandidateNote,
    PipelineStage, RequisitionStatus
)
from backend.app.modules.recruitment.schemas import (
    RequisitionCreate, CandidateCreate, StageTransitionRequest, ScorecardCreate,
    CandidateNoteCreate
)
from backend.app.core.workflow_engine import WORKFLOW_REGISTRY, TransitionError
from backend.app.core.event_bus import event_bus, DomainEvent, EventTypes


def _get_val(enum_or_str: Any) -> str:
    return enum_or_str.value if hasattr(enum_or_str, "value") else str(enum_or_str)


class RecruitmentService:

    @staticmethod
    async def create_requisition(session: AsyncSession, data: RequisitionCreate, tenant_id: str) -> JobRequisition:
        if not data.code:
            count_res = await session.execute(select(func.count(JobRequisition.id)).where(JobRequisition.tenant_id == tenant_id))
            c = count_res.scalar() or 0
            code = f"REQ-{2001 + c}"
        else:
            code = data.code

        req = JobRequisition(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=data.title,
            code=code,
            department_id=data.department_id,
            hiring_manager_id=data.hiring_manager_id,
            open_positions=data.open_positions,
            status=RequisitionStatus.OPEN,
            location=data.location,
            experience_years_min=data.experience_years_min,
            min_budget=data.min_budget,
            max_budget=data.max_budget,
            currency=data.currency,
            job_description=data.job_description,
            required_skills=data.required_skills
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)
        return req

    @staticmethod
    async def list_requisitions(session: AsyncSession, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(JobRequisition, func.count(CandidateApplication.id).label("applicant_count"))
            .outerjoin(CandidateApplication, JobRequisition.id == CandidateApplication.requisition_id)
            .where(JobRequisition.tenant_id == tenant_id)
            .group_by(JobRequisition.id)
            .order_by(JobRequisition.created_at.desc())
        )
        result = await session.execute(stmt)
        reqs = []
        for req, count in result.all():
            d = req.to_dict()
            d["applicant_count"] = count
            reqs.append(d)
        return reqs

    @staticmethod
    async def create_candidate(session: AsyncSession, data: CandidateCreate, tenant_id: str, actor_id: str) -> Candidate:
        candidate = Candidate(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            current_company=data.current_company,
            current_title=data.current_title,
            years_of_experience=data.years_of_experience,
            skills_tags=data.skills_tags,
            source=data.source,
            resume_url=data.resume_url
        )
        session.add(candidate)
        await session.flush()

        if data.requisition_id:
            application = CandidateApplication(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                candidate_id=candidate.id,
                requisition_id=data.requisition_id,
                stage=PipelineStage.APPLIED
            )
            session.add(application)

        await session.commit()
        await session.refresh(candidate)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.CANDIDATE_APPLIED,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload={"id": candidate.id, "name": candidate.full_name, "email": candidate.email}
        ))
        return candidate

    @staticmethod
    async def get_kanban_board(session: AsyncSession, requisition_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Returns structured Kanban columns with candidate cards and match scores."""
        stages = [
            ("applied", "New Applied"),
            ("screening", "Screening"),
            ("interviewing", "Interviews"),
            ("tech_assessment", "Technical Round"),
            ("offer_extended", "Offer Sent"),
            ("hired", "Hired 🎉"),
            ("rejected", "Disqualified")
        ]

        stmt = (
            select(CandidateApplication)
            .options(
                selectinload(CandidateApplication.candidate),
                selectinload(CandidateApplication.scorecards)
            )
            .where(
                CandidateApplication.requisition_id == requisition_id,
                CandidateApplication.tenant_id == tenant_id
            )
        )
        result = await session.execute(stmt)
        apps = result.scalars().all()

        columns = []
        for stage_key, stage_label in stages:
            stage_apps = [a for a in apps if _get_val(a.stage) == stage_key]
            app_cards = []
            for a in stage_apps:
                app_cards.append({
                    "application_id": a.id,
                    "candidate_id": a.candidate.id,
                    "name": a.candidate.full_name,
                    "email": a.candidate.email,
                    "title": a.candidate.current_title or "Applicant",
                    "experience_years": a.candidate.years_of_experience,
                    "skills": [s.strip() for s in a.candidate.skills_tags.split(",") if s.strip()],
                    "source": _get_val(a.candidate.source),
                    "ai_match_score": a.candidate.ai_match_score,
                    "scorecards_count": len(a.scorecards),
                    "overall_rating": a.overall_rating
                })

            columns.append({
                "stage": stage_key,
                "label": stage_label,
                "count": len(app_cards),
                "applications": app_cards
            })

        return columns

    @staticmethod
    async def transition_stage(
        session: AsyncSession,
        application_id: str,
        target_stage: PipelineStage,
        actor_id: str,
        actor_roles: set,
        tenant_id: str,
        rejection_reason: Optional[str] = None
    ) -> CandidateApplication:
        stmt = (
            select(CandidateApplication)
            .options(selectinload(CandidateApplication.candidate))
            .where(CandidateApplication.id == application_id, CandidateApplication.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        app = result.scalar_one_or_none()
        if not app:
            raise ValueError("Candidate application not found")

        current_stage = _get_val(app.stage)
        target_stage_val = _get_val(target_stage)
        workflow = WORKFLOW_REGISTRY["recruitment_pipeline"]

        if not workflow.can_transition(current_stage, target_stage_val, actor_roles):
            raise TransitionError(f"Cannot move application from '{current_stage}' to '{target_stage_val}'")

        app.stage = target_stage
        app.stage_updated_at = datetime.now(timezone.utc)
        if rejection_reason:
            app.rejection_reason = rejection_reason

        await session.commit()
        await session.refresh(app)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.STAGE_TRANSITIONED,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload={
                "application_id": app.id,
                "candidate_name": app.candidate.full_name,
                "from_stage": current_stage,
                "to_stage": target_stage_val
            }
        ))
        return app

    @staticmethod
    async def submit_scorecard(
        session: AsyncSession,
        application_id: str,
        data: ScorecardCreate,
        tenant_id: str,
        actor_id: str
    ) -> InterviewScorecard:
        scorecard = InterviewScorecard(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            interviewer_id=data.interviewer_id,
            round_name=data.round_name,
            technical_score=data.technical_score,
            communication_score=data.communication_score,
            cultural_fit_score=data.cultural_fit_score,
            recommendation=data.recommendation,
            feedback_notes=data.feedback_notes
        )
        session.add(scorecard)

        avg_score = (data.technical_score + data.communication_score + data.cultural_fit_score) / 3.0
        stmt = select(CandidateApplication).where(CandidateApplication.id == application_id)
        res = await session.execute(stmt)
        app = res.scalar_one_or_none()
        if app:
            app.overall_rating = round(avg_score, 1)

        await session.commit()
        await session.refresh(scorecard)
        return scorecard

    @staticmethod
    async def list_candidates(
        session: AsyncSession,
        tenant_id: str,
        search: Optional[str] = None,
        source: Optional[str] = None,
        min_exp: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Searchable Talent Pool Directory across all candidate leads."""
        stmt = (
            select(Candidate)
            .options(
                selectinload(Candidate.applications),
                selectinload(Candidate.notes)
            )
            .where(Candidate.tenant_id == tenant_id)
            .order_by(Candidate.created_at.desc())
        )
        if source:
            stmt = stmt.where(Candidate.source == source)
        if min_exp is not None:
            stmt = stmt.where(Candidate.years_of_experience >= min_exp)

        result = await session.execute(stmt)
        candidates = result.scalars().all()

        output = []
        for c in candidates:
            if search:
                q = search.lower()
                matched = (
                    q in c.first_name.lower() or
                    q in c.last_name.lower() or
                    q in c.email.lower() or
                    q in (c.current_company or "").lower() or
                    q in (c.current_title or "").lower() or
                    q in (c.skills_tags or "").lower()
                )
                if not matched:
                    continue

            output.append({
                "id": c.id,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "full_name": c.full_name,
                "email": c.email,
                "phone": c.phone,
                "current_company": c.current_company,
                "current_title": c.current_title,
                "years_of_experience": c.years_of_experience,
                "skills_tags": c.skills_tags,
                "source": _get_val(c.source),
                "ai_match_score": c.ai_match_score,
                "application_count": len(c.applications),
                "notes_count": len(c.notes),
                "created_at": c.created_at
            })
        return output

    @staticmethod
    async def get_candidate_detail(session: AsyncSession, candidate_id: str, tenant_id: str) -> Dict[str, Any]:
        """Fetches full candidate CRM profile with notes, applications & scorecards."""
        stmt = (
            select(Candidate)
            .options(
                selectinload(Candidate.applications).selectinload(CandidateApplication.requisition),
                selectinload(Candidate.applications).selectinload(CandidateApplication.scorecards),
                selectinload(Candidate.notes)
            )
            .where(Candidate.id == candidate_id, Candidate.tenant_id == tenant_id)
        )
        result = await session.execute(stmt)
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise ValueError("Candidate not found")

        apps_data = []
        for app in candidate.applications:
            apps_data.append({
                "id": app.id,
                "requisition_id": app.requisition_id,
                "requisition_code": app.requisition.code if app.requisition else None,
                "requisition_title": app.requisition.title if app.requisition else None,
                "stage": _get_val(app.stage),
                "overall_rating": app.overall_rating,
                "stage_updated_at": app.stage_updated_at.isoformat() if app.stage_updated_at else None,
                "rejection_reason": app.rejection_reason,
                "scorecards": [
                    {
                        "id": sc.id,
                        "round_name": sc.round_name,
                        "technical_score": sc.technical_score,
                        "communication_score": sc.communication_score,
                        "cultural_fit_score": sc.cultural_fit_score,
                        "recommendation": sc.recommendation,
                        "feedback_notes": sc.feedback_notes
                    }
                    for sc in app.scorecards
                ]
            })

        notes_data = [
            {
                "id": n.id,
                "candidate_id": n.candidate_id,
                "author_id": n.author_id,
                "author_name": n.author_name,
                "note_type": n.note_type,
                "content": n.content,
                "created_at": n.created_at
            }
            for n in sorted(candidate.notes, key=lambda x: x.created_at, reverse=True)
        ]

        return {
            "id": candidate.id,
            "first_name": candidate.first_name,
            "last_name": candidate.last_name,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_company": candidate.current_company,
            "current_title": candidate.current_title,
            "years_of_experience": candidate.years_of_experience,
            "skills_tags": candidate.skills_tags,
            "source": _get_val(candidate.source),
            "resume_url": candidate.resume_url,
            "ai_match_score": candidate.ai_match_score,
            "applications": apps_data,
            "notes": notes_data,
            "created_at": candidate.created_at
        }

    @staticmethod
    async def add_candidate_note(
        session: AsyncSession,
        candidate_id: str,
        data: CandidateNoteCreate,
        tenant_id: str,
        author_id: str,
        author_name: str
    ) -> CandidateNote:
        """Logs recruiter interaction note / CRM touchpoint."""
        cand_stmt = select(Candidate).where(Candidate.id == candidate_id, Candidate.tenant_id == tenant_id)
        cand_res = await session.execute(cand_stmt)
        if not cand_res.scalar_one_or_none():
            raise ValueError("Candidate not found")

        note = CandidateNote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            author_id=author_id,
            author_name=author_name,
            note_type=data.note_type,
            content=data.content
        )
        session.add(note)
        await session.commit()
        await session.refresh(note)
        return note

    @staticmethod
    async def list_candidate_notes(session: AsyncSession, candidate_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Retrieves chronological activity timeline for candidate."""
        stmt = (
            select(CandidateNote)
            .where(CandidateNote.candidate_id == candidate_id, CandidateNote.tenant_id == tenant_id)
            .order_by(CandidateNote.created_at.desc())
        )
        res = await session.execute(stmt)
        notes = res.scalars().all()
        return [
            {
                "id": n.id,
                "candidate_id": n.candidate_id,
                "author_id": n.author_id,
                "author_name": n.author_name,
                "note_type": n.note_type,
                "content": n.content,
                "created_at": n.created_at
            }
            for n in notes
        ]

    @staticmethod
    async def get_pipeline_analytics(session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        """Calculates recruitment CRM funnel metrics and sourcing attribution."""
        cand_res = await session.execute(select(Candidate).where(Candidate.tenant_id == tenant_id))
        candidates = cand_res.scalars().all()

        app_res = await session.execute(select(CandidateApplication).where(CandidateApplication.tenant_id == tenant_id))
        applications = app_res.scalars().all()

        total_cands = len(candidates)
        total_apps = len(applications)

        stage_breakdown = {
            "applied": 0,
            "screening": 0,
            "interviewing": 0,
            "tech_assessment": 0,
            "offer_extended": 0,
            "offer_accepted": 0,
            "hired": 0,
            "rejected": 0
        }
        for a in applications:
            st = _get_val(a.stage)
            if st in stage_breakdown:
                stage_breakdown[st] += 1

        source_attribution: Dict[str, int] = {}
        ai_scores = []
        for c in candidates:
            src = _get_val(c.source)
            source_attribution[src] = source_attribution.get(src, 0) + 1
            if c.ai_match_score > 0:
                ai_scores.append(c.ai_match_score)

        avg_ai = round(sum(ai_scores) / len(ai_scores), 1) if ai_scores else 0.0

        applied_count = max(total_apps, 1)
        interview_count = stage_breakdown["interviewing"] + stage_breakdown["tech_assessment"] + stage_breakdown["offer_extended"] + stage_breakdown["offer_accepted"] + stage_breakdown["hired"]
        offer_count = stage_breakdown["offer_extended"] + stage_breakdown["offer_accepted"] + stage_breakdown["hired"]
        hire_count = stage_breakdown["hired"]

        conversion_rates = {
            "interview_rate": round((interview_count / applied_count) * 100, 1),
            "offer_rate": round((offer_count / applied_count) * 100, 1),
            "hire_rate": round((hire_count / applied_count) * 100, 1)
        }

        return {
            "total_candidates": total_cands,
            "total_applications": total_apps,
            "stage_breakdown": stage_breakdown,
            "source_attribution": source_attribution,
            "avg_ai_match_score": avg_ai,
            "conversion_rates": conversion_rates
        }
