import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.parsers.resume_parser import parse_jd
from src.scoring.scorer import evaluate_candidate
from data.sample_data import SAMPLE_JD, SAMPLE_RESUMES
from pathlib import Path
import json

jd = parse_jd(SAMPLE_JD)
results = []
for name, text in SAMPLE_RESUMES.items():
    res = evaluate_candidate(text, name, jd)
    results.append(res)
results.sort(key=lambda r: r.final_score, reverse=True)

out = []
for r in results:
    out.append({
        "candidate_name": r.candidate_name,
        "final_score": r.final_score,
        "scores": {
            "skills_match": r.scores.skills_match.score,
            "experience_relevance": r.scores.experience_relevance.score,
            "education_certs": r.scores.education_certs.score,
            "project_portfolio": r.scores.project_portfolio.score,
            "communication_quality": r.scores.communication_quality.score,
        },
        "recommendation": r.hire_recommendation.value,
        "executive_summary": r.executive_summary,
    })

Path("data").mkdir(exist_ok=True)
with open("data/auto_run_results.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)

print("Wrote data/auto_run_results.json")
