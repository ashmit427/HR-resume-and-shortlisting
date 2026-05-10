"""
Scoring Engine — scores candidates against JD.
Uses unified llm_client — works with Anthropic OR HuggingFace.
Innovations:
  1. Bias Audit (blind vs normal scoring)
  2. Auto Interview Question Generation
  3. Personality Insight from writing style
"""
import json
import re
import ast
from pathlib import Path
from src.llm_client import llm_json, llm_call
from src.schemas import (
    RubricScores, DimensionScore, BiasAuditResult,
    InterviewQuestion, PersonalityInsight,
    CandidateProfile, JDRequirements, HireRecommendation,
    CandidateResult,
)
from src.parsers.resume_parser import anonymize_resume, parse_candidate_profile

SCORING_SYSTEM = (
    "You are an expert, objective HR evaluator. Score candidates strictly on evidence. "
    "Never inflate scores. Output ONLY valid JSON. No markdown. No preamble."
)


def score_resume_against_jd(resume_text: str, jd: JDRequirements, blind_mode: bool = False) -> RubricScores:
    mode_note = "(BLIND MODE — name, college, gender info removed for fairness)" if blind_mode else ""
    rubric = f"""Role: {jd.role_title} | Domain: {jd.domain} | Seniority: {jd.seniority_level}
Required skills: {', '.join(jd.required_skills)}
Preferred skills: {', '.join(jd.preferred_skills)}
Min experience: {jd.min_experience_years} years | Education: {jd.education_requirement}
Responsibilities: {'; '.join(jd.key_responsibilities[:4])}"""

    prompt = f"""{SCORING_SYSTEM}
{mode_note}

JOB REQUIREMENTS:
{rubric}

CANDIDATE RESUME:
{resume_text[:3500]}

Score EXACTLY these 5 dimensions (0.0-10.0 each). Return ONLY this JSON:
{{
  "skills_match": {{"score": 7.5, "justification": "one line", "evidence": "direct quote"}},
  "experience_relevance": {{"score": 6.0, "justification": "one line", "evidence": "direct quote"}},
  "education_certs": {{"score": 8.0, "justification": "one line", "evidence": "direct quote"}},
  "project_portfolio": {{"score": 7.0, "justification": "one line", "evidence": "direct quote"}},
  "communication_quality": {{"score": 8.5, "justification": "one line", "evidence": "direct quote"}}
}}"""

    try:
        data = llm_json(prompt, max_tokens=900)
    except Exception as e:
        print(f"⚠️  Scoring LLM failed: {e} — using default neutral scores")
        data = {}

    # Ensure we have a dict with the required keys; fill safe defaults for missing fields
    if not isinstance(data, dict):
        data = {}

    def default_dim(score=5.0):
        return {
            "score": score,
            "justification": "Auto-defaulted due to missing or malformed LLM output.",
            "evidence": "No explicit evidence available.",
        }

    skills = data.get("skills_match") or default_dim(5.0)
    exp = data.get("experience_relevance") or default_dim(5.0)
    edu = data.get("education_certs") or default_dim(5.0)
    proj = data.get("project_portfolio") or default_dim(5.0)
    comm = data.get("communication_quality") or default_dim(5.0)

    # Coerce numeric scores if they come as strings or are missing
    for d in (skills, exp, edu, proj, comm):
        try:
            d["score"] = float(d.get("score", 5.0))
        except Exception:
            d["score"] = 5.0

    try:
        return RubricScores(
            skills_match=DimensionScore(**skills),
            experience_relevance=DimensionScore(**exp),
            education_certs=DimensionScore(**edu),
            project_portfolio=DimensionScore(**proj),
            communication_quality=DimensionScore(**comm),
        )
    except Exception as e:
        print(f"⚠️  Building RubricScores failed: {e} — returning neutral defaults")
        d = default_dim(5.0)
        return RubricScores(
            skills_match=DimensionScore(**d),
            experience_relevance=DimensionScore(**d),
            education_certs=DimensionScore(**d),
            project_portfolio=DimensionScore(**d),
            communication_quality=DimensionScore(**d),
        )


def run_bias_audit(resume_text: str, normal_scores: RubricScores, jd: JDRequirements) -> BiasAuditResult:
    """Innovation 1: Blind vs normal scoring comparison."""
    blind_text = anonymize_resume(resume_text)
    blind_scores = score_resume_against_jd(blind_text, jd, blind_mode=True)

    normal_total = normal_scores.weighted_total
    blind_total = blind_scores.weighted_total
    drift = round(abs(normal_total - blind_total), 2)
    drift_pct = round((drift / max(normal_total, 0.1)) * 100, 1)
    bias_flag = drift_pct > 10.0

    signals = []
    for p in ["IIT", "IIM", "Harvard", "Oxford", "Stanford", "MIT", "Cambridge"]:
        if p.lower() in resume_text.lower():
            signals.append(f"Prestige institution: {p}")
    if re.search(r"\b(he|she|his|her)\b", resume_text, re.IGNORECASE):
        signals.append("Gender pronouns in resume")

    fairness = "GREEN" if drift_pct <= 5 else ("YELLOW" if drift_pct <= 10 else "RED")
    note = (
        f"Score dropped {drift:.1f} pts ({drift_pct}%) in blind mode — potential bias."
        if bias_flag
        else f"Consistent in blind mode (drift: {drift:.1f} pts, {drift_pct}%). Fair evaluation."
    )

    return BiasAuditResult(
        normal_score=normal_total, blind_score=blind_total,
        score_drift=drift, drift_percentage=drift_pct,
        bias_flag=bias_flag, bias_signals_detected=signals,
        fairness_index=fairness, auditor_note=note,
    )


def generate_interview_questions(profile: CandidateProfile, scores: RubricScores, jd: JDRequirements) -> list[InterviewQuestion]:
    """Innovation 2: Gap-targeted interview questions."""
    dim_scores = {
        "Skills Match": scores.skills_match.score,
        "Experience Relevance": scores.experience_relevance.score,
        "Education & Certs": scores.education_certs.score,
        "Project/Portfolio": scores.project_portfolio.score,
        "Communication Quality": scores.communication_quality.score,
    }
    weak = sorted(dim_scores.items(), key=lambda x: x[1])[:3]
    missing = list(set(jd.required_skills) - set(profile.skills))[:5]

    prompt = f"""You are a senior technical interviewer. Generate 3 targeted interview questions.

CANDIDATE: {profile.name} | ROLE: {jd.role_title} ({jd.seniority_level})
Weak dimensions: {', '.join([f'{d}: {s}/10' for d, s in weak])}
Their skills: {', '.join(profile.skills[:10])}
Missing required skills: {', '.join(missing)}
Their projects: {'; '.join(profile.projects[:2])}

Return ONLY a JSON array of 3 objects:
[
  {{
    "question": "Specific question referencing their resume...",
    "dimension_targeted": "Skills Match",
    "why_this_question": "Short reason...",
    "red_flag_answer": "What a bad answer looks like...",
    "green_flag_answer": "What a great answer looks like..."
  }}
]"""

    try:
        data = llm_json(prompt, max_tokens=1200)
    except Exception:
        data = None

    # Normalize various LLM return shapes into a list of dicts
    def normalize_to_dict_list(raw):
        if raw is None:
            return []
        if isinstance(raw, dict):
            # If dict is numeric-keyed ("0", "1"), return sorted values
            if all(isinstance(k, str) and k.isdigit() for k in raw.keys()):
                return [v for k, v in sorted(raw.items(), key=lambda x: int(x[0]))]
            return [raw]
        if isinstance(raw, list):
            out = []
            for item in raw:
                if isinstance(item, dict):
                    out.append(item)
                elif isinstance(item, str):
                    # try to parse JSON string
                    parsed = None
                    try:
                        parsed = json.loads(item)
                    except Exception:
                        try:
                            parsed = ast.literal_eval(item)
                        except Exception:
                            parsed = None
                    if isinstance(parsed, dict):
                        out.append(parsed)
                    elif isinstance(parsed, list):
                        out.extend(parsed)
                    else:
                        out.append({"question": item})
                else:
                    out.append({"question": str(item)})
            return out
        if isinstance(raw, str):
            # try to parse a JSON array/object from the string
            try:
                parsed = json.loads(raw)
                return normalize_to_dict_list(parsed)
            except Exception:
                try:
                    parsed = ast.literal_eval(raw)
                    return normalize_to_dict_list(parsed)
                except Exception:
                    return [{"question": raw}]
        return [{"question": str(raw)}]

    data_list = normalize_to_dict_list(data)

    questions = []
    if data_list:
        for q in data_list[:3]:
            if not isinstance(q, dict):
                q = {"question": str(q)}
            try:
                questions.append(InterviewQuestion(**{
                    "question": q.get("question") or q.get("q") or q.get("prompt", "Describe a relevant project from your resume."),
                    "dimension_targeted": q.get("dimension_targeted", q.get("dimension", "Skills Match")),
                    "why_this_question": q.get("why_this_question", q.get("why", "Probe for demonstrated experience.")),
                    "red_flag_answer": q.get("red_flag_answer", "Vague or no specifics."),
                    "green_flag_answer": q.get("green_flag_answer", "Clear measurable outcomes and ownership."),
                }))
            except Exception:
                questions.append(InterviewQuestion(
                    question=q.get("question", "Describe a relevant project from your resume."),
                    dimension_targeted=q.get("dimension_targeted", "Skills Match"),
                    why_this_question=q.get("why_this_question", "Probe for demonstrated experience."),
                    red_flag_answer=q.get("red_flag_answer", "Vague or no specifics."),
                    green_flag_answer=q.get("green_flag_answer", "Clear measurable outcomes and ownership."),
                ))
    else:
        # Default generic questions
        missing = list(set(jd.required_skills) - set(profile.skills))[:3]
        for m in missing or [None, None, None]:
            topic = m or "their recent projects"
            questions.append(InterviewQuestion(
                question=f"Tell me about a project where you worked on {topic}.",
                dimension_targeted="Skills Match",
                why_this_question="Checks for hands-on experience and impact.",
                red_flag_answer="Cannot describe concrete contributions or outcomes.",
                green_flag_answer="Describes scope, actions, and measurable results.",
            ))

    return questions


def generate_personality_insights(resume_text: str) -> list[PersonalityInsight]:
    """Innovation 3: Writing-style personality signal extraction."""
    prompt = f"""Analyze ONLY the writing style and word choice in this resume to infer 3 soft-skill signals.
Focus on HOW they write (active vs passive, quantification, ownership language).
NOT demographics.

RESUME:
{resume_text[:2000]}

Return ONLY a JSON array of 3 objects:
[
  {{
    "trait": "Ownership Mindset",
    "signal": "Uses I built, I led, I designed throughout",
    "confidence": "High"
  }}
]"""

    try:
        data = llm_json(prompt, max_tokens=700)
    except Exception:
        data = None

    def normalize_personality(raw):
        if raw is None:
            return []
        if isinstance(raw, dict):
            return [raw]
        if isinstance(raw, list):
            out = []
            for item in raw:
                if isinstance(item, dict):
                    out.append(item)
                elif isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                    except Exception:
                        try:
                            parsed = ast.literal_eval(item)
                        except Exception:
                            parsed = None
                    if isinstance(parsed, dict):
                        out.append(parsed)
                    elif isinstance(parsed, list):
                        out.extend(parsed)
                    else:
                        out.append({"trait": item, "signal": "No signal", "confidence": "Low"})
            return out
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                return normalize_personality(parsed)
            except Exception:
                try:
                    parsed = ast.literal_eval(raw)
                    return normalize_personality(parsed)
                except Exception:
                    return [{"trait": raw, "signal": "No signal", "confidence": "Low"}]
        return [{"trait": str(raw), "signal": "No signal", "confidence": "Low"}]

    data_list = normalize_personality(data)

    insights = []
    if data_list:
        for p in data_list[:3]:
            if not isinstance(p, dict):
                p = {"trait": str(p), "signal": "No signal", "confidence": "Low"}
            try:
                insights.append(PersonalityInsight(**p))
            except Exception:
                insights.append(PersonalityInsight(trait=p.get("trait", "Unknown"), signal=p.get("signal", "No signal"), confidence=p.get("confidence", "Low")))
    else:
        insights = [PersonalityInsight(trait="Neutral", signal="No strong signals.", confidence="Low")]

    return insights


def generate_executive_summary(profile: CandidateProfile, scores: RubricScores, jd: JDRequirements, recommendation: HireRecommendation) -> tuple[str, list[str], list[str]]:
    prompt = f"""Write a 3-sentence executive summary for an HR shortlist report.
Candidate: {profile.name} | Role: {jd.role_title}
Score: {scores.weighted_total}/10 | Recommendation: {recommendation.value}

Return ONLY JSON:
{{
  "summary": "3 sentence summary...",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "concerns": ["concern 1", "concern 2"]
}}"""

    try:
        data = llm_json(prompt, max_tokens=600)
    except Exception:
        data = None

    if not isinstance(data, dict):
        # Safe defaults
        return (
            f"{profile.name} — no executive summary available.",
            ["Skills: not assessed"],
            ["No concerns noted."],
        )

    summary = data.get("summary", f"{profile.name} — summary not generated.")
    strengths = data.get("strengths", ["Not provided"]) or ["Not provided"]
    concerns = data.get("concerns", ["Not provided"]) or ["Not provided"]
    return summary, strengths, concerns


def determine_recommendation(score: float) -> HireRecommendation:
    if score >= 8.5: return HireRecommendation.STRONG_YES
    elif score >= 7.0: return HireRecommendation.YES
    elif score >= 5.5: return HireRecommendation.MAYBE
    elif score >= 4.0: return HireRecommendation.NO
    else: return HireRecommendation.STRONG_NO


def evaluate_candidate(resume_text: str, source_file: str, jd: JDRequirements) -> CandidateResult:
    """Full evaluation pipeline for one candidate."""
    profile = parse_candidate_profile(resume_text)
    # If parser couldn't extract a sensible name, prefer the uploaded filename (without extension)
    fallback_name = None
    try:
        if source_file:
            fallback_name = Path(source_file).stem
    except Exception:
        fallback_name = None

    bad_names = {None, "", "unknown", "unknown candidate", "candidate", "string", "n/a"}
    parsed_name = (profile.name or "").strip()
    parsed_name_norm = re.sub(r"[^a-zA-Z ]", "", parsed_name).strip().lower()
    if (not parsed_name) or (parsed_name_norm in bad_names) or parsed_name.startswith("[candidate") or len(parsed_name) < 2:
        if fallback_name:
            profile.name = fallback_name
    scores = score_resume_against_jd(resume_text, jd)
    weighted = scores.weighted_total
    bias_audit = run_bias_audit(resume_text, scores, jd)
    recommendation = determine_recommendation(weighted)
    try:
        summary, strengths, concerns = generate_executive_summary(profile, scores, jd, recommendation)
    except Exception as e:
        print(f"⚠️  Executive summary generation failed: {e} — using defaults")
        summary = f"{profile.name} — summary not available."
        strengths = ["Not provided"]
        concerns = ["Not provided"]

    try:
        interview_qs = generate_interview_questions(profile, scores, jd)
    except Exception as e:
        print(f"⚠️  Interview question generation failed: {e} — using defaults")
        interview_qs = []

    try:
        personality = generate_personality_insights(resume_text)
    except Exception as e:
        print(f"⚠️  Personality insight generation failed: {e} — using defaults")
        personality = [PersonalityInsight(trait="Neutral", signal="No strong signals.", confidence="Low")]

    return CandidateResult(
        candidate_name=profile.name,
        source_file=source_file,
        profile=profile,
        scores=scores,
        weighted_total=weighted,
        hire_recommendation=recommendation,
        executive_summary=summary,
        strengths=strengths,
        concerns=concerns,
        bias_audit=bias_audit,
        interview_questions=interview_qs,
        personality_insights=personality,
    )
