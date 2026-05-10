import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.parsers.resume_parser import parse_jd
from src.scoring.scorer import evaluate_candidate
from data.sample_data import SAMPLE_JD, SAMPLE_RESUMES

jd = parse_jd(SAMPLE_JD)

for fname, text in SAMPLE_RESUMES.items():
    print('\n===', fname)
    result = evaluate_candidate(text, fname, jd)
    print('Name:', result.candidate_name)
    print('Weighted total:', result.weighted_total)
    print('Scores:')
    print('  Skills:', result.scores.skills_match.score)
    print('  Experience:', result.scores.experience_relevance.score)
    print('  Education:', result.scores.education_certs.score)
    print('  Project:', result.scores.project_portfolio.score)
    print('  Communication:', result.scores.communication_quality.score)
    print('Recommendation:', result.hire_recommendation)
    print('Executive summary:', result.executive_summary)
