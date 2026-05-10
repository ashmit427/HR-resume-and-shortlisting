"""
Pydantic schemas for all structured LLM outputs.
Using strict typing prevents hallucination and parsing errors.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class HireRecommendation(str, Enum):
    STRONG_YES = "Strong Yes"
    YES = "Yes"
    MAYBE = "Maybe - Needs Review"
    NO = "No"
    STRONG_NO = "Strong No"


class DimensionScore(BaseModel):
    score: float = Field(ge=0, le=10, description="Score from 0-10")
    justification: str = Field(min_length=10, max_length=300)
    evidence: str = Field(description="Direct evidence from resume/profile")

    @field_validator("score")
    @classmethod
    def round_score(cls, v):
        return round(v, 1)


class RubricScores(BaseModel):
    skills_match: DimensionScore
    experience_relevance: DimensionScore
    education_certs: DimensionScore
    project_portfolio: DimensionScore
    communication_quality: DimensionScore

    @property
    def weighted_total(self) -> float:
        weights = {
            "skills_match": 0.30,
            "experience_relevance": 0.25,
            "education_certs": 0.15,
            "project_portfolio": 0.20,
            "communication_quality": 0.10,
        }
        total = (
            self.skills_match.score * weights["skills_match"]
            + self.experience_relevance.score * weights["experience_relevance"]
            + self.education_certs.score * weights["education_certs"]
            + self.project_portfolio.score * weights["project_portfolio"]
            + self.communication_quality.score * weights["communication_quality"]
        )
        return round(total, 2)


class BiasAuditResult(BaseModel):
    """Innovation 1: Bias detection by comparing blind vs normal scoring"""
    normal_score: float
    blind_score: float
    score_drift: float
    drift_percentage: float
    bias_flag: bool
    bias_signals_detected: list[str] = Field(
        description="Names, colleges, gender markers found"
    )
    fairness_index: str = Field(description="GREEN / YELLOW / RED")
    auditor_note: str


class InterviewQuestion(BaseModel):
    """Innovation 2: AI-generated targeted interview questions per candidate gap"""
    question: str
    dimension_targeted: str
    why_this_question: str
    red_flag_answer: str
    green_flag_answer: str


class PersonalityInsight(BaseModel):
    """Innovation 3: Soft-skill personality signal extracted from writing style"""
    trait: str
    signal: str
    confidence: str  # Low / Medium / High


class CandidateProfile(BaseModel):
    """Parsed structured candidate data"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    years_experience: float
    current_role: Optional[str] = None
    skills: list[str]
    education: list[str]
    certifications: list[str]
    projects: list[str]
    summary_text: str


class JDRequirements(BaseModel):
    """Parsed Job Description"""
    role_title: str
    required_skills: list[str]
    preferred_skills: list[str]
    min_experience_years: float
    education_requirement: str
    key_responsibilities: list[str]
    domain: str
    seniority_level: str


class CandidateResult(BaseModel):
    """Full result for one candidate — the complete output object"""
    candidate_name: str
    source_file: str
    profile: CandidateProfile
    scores: RubricScores
    weighted_total: float
    hire_recommendation: HireRecommendation
    executive_summary: str = Field(max_length=400)
    strengths: list[str]
    concerns: list[str]

    # Innovation 1
    bias_audit: BiasAuditResult

    # Innovation 2
    interview_questions: list[InterviewQuestion]

    # Innovation 3
    personality_insights: list[PersonalityInsight]

    # HR override fields
    hr_override_score: Optional[float] = None
    hr_override_reason: Optional[str] = None
    hr_override_by: Optional[str] = None

    @property
    def final_score(self) -> float:
        return self.hr_override_score if self.hr_override_score else self.weighted_total
