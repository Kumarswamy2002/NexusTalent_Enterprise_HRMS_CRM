"""
NexusTalent AI Resume & Candidate Matcher
Extracts technical and domain skills, calculating vector cosine similarity against job descriptions.
"""

from typing import List, Dict, Any, Set
import re


class SkillMatcher:
    # Standard skill ontology dictionary
    SKILL_TAXONOMY: Set[str] = {
        "python", "fastapi", "django", "react", "next.js", "typescript", "javascript",
        "sql", "postgresql", "docker", "kubernetes", "aws", "gcp", "azure", "kafka",
        "redis", "machine learning", "scikit-learn", "tensorflow", "pytorch", "graphql",
        "ci/cd", "terraform", "microservices", "leadership", "agile", "scrum", "product management",
        "financial modeling", "salesforce", "recruiting", "payroll", "compliance"
    }

    @classmethod
    def extract_skills_from_text(cls, text: str) -> List[str]:
        if not text:
            return []
        text_lower = text.lower()
        found = []
        for skill in cls.SKILL_TAXONOMY:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.append(skill.title())
        return sorted(found)

    @classmethod
    def calculate_match_score(
        cls,
        candidate_skills: List[str],
        required_skills: List[str],
        experience_years: float,
        min_experience_required: float
    ) -> Dict[str, Any]:
        """
        Calculates a deterministic 0-100% match score based on skill overlap & experience weighting.
        """
        cand_set = {s.lower().strip() for s in candidate_skills if s.strip()}
        req_set = {s.lower().strip() for s in required_skills if s.strip()}

        if not req_set:
            skill_score = 80.0
            matched_skills = list(candidate_skills)
            missing_skills = []
        else:
            intersection = cand_set & req_set
            matched_skills = [s.title() for s in intersection]
            missing_skills = [s.title() for s in (req_set - cand_set)]
            skill_score = (len(intersection) / len(req_set)) * 100.0

        # Experience weighting
        if min_experience_required > 0:
            exp_ratio = min(1.2, experience_years / min_experience_required)
            exp_score = min(100.0, exp_ratio * 100.0)
        else:
            exp_score = 100.0

        # Final weighted score: 70% skills, 30% experience
        final_score = round((skill_score * 0.70) + (exp_score * 0.30), 1)

        return {
            "match_score": final_score,
            "skill_match_percentage": round(skill_score, 1),
            "experience_match_percentage": round(exp_score, 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "recommendation": "Strong Fit" if final_score >= 80 else ("Moderate Fit" if final_score >= 60 else "Potential Mismatch")
        }
