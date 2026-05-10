

import streamlit as st
import json
import tempfile
import os
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

# Page config MUST be first
st.set_page_config(
    page_title="TalentLens AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --ink: #0f0e17;
    --cream: #fffcf2;
    --accent: #ff6b35;
    --accent2: #2ec4b6;
    --muted: #5c5c7a;
    --card-bg: #ffffff;
    --border: #e8e4d9;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
    background: var(--cream);
}

h1, h2, h3 { font-family: 'Syne', sans-serif; }

.main-header {
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -2px;
    line-height: 1;
    background: linear-gradient(135deg, #0f0e17 0%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.tagline {
    font-size: 1rem;
    color: var(--muted);
    margin-top: 4px;
    letter-spacing: 0.5px;
}

.score-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    font-family: 'Syne', sans-serif;
}

.score-strong-yes { background: #d4edda; color: #155724; }
.score-yes { background: #cce5ff; color: #004085; }
.score-maybe { background: #fff3cd; color: #856404; }
.score-no { background: #f8d7da; color: #721c24; }

.metric-card {
    background: #1a1a1a;
    border: 1px solid #444;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 4px;
    color: #e8e4d9;
}

.metric-num {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--accent);
    line-height: 1;
}

.metric-label {
    font-size: 0.8rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

.candidate-card {
    background: #1a1a1a;
    border: 1px solid #444;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    transition: box-shadow 0.2s;
    position: relative;
    overflow: hidden;
    color: #e8e4d9;
}

.candidate-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    border-radius: 4px 0 0 4px;
}

.rank-1::before { background: #ffd700; }
.rank-2::before { background: #c0c0c0; }
.rank-3::before { background: #cd7f32; }
.rank-other::before { background: var(--border); }

.bias-green { background: #1e7e34; color: #ffffff; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; }
.bias-yellow { background: #997404; color: #ffffff; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; }
.bias-red { background: #842029; color: #ffffff; padding: 4px 10px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; }

.innovation-tag {
    background: var(--accent);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    font-family: 'Syne', sans-serif;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 8px;
}

.progress-bar-bg {
    background: #f0ede6;
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
}

.q-card {
    background: #f8f7f4;
    border-left: 3px solid var(--accent);
    padding: 14px 16px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
}

.sidebar-brand {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}

/* Hide streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ── Imports after page config ─────────────────────────────────────────────────
from src.parsers.resume_parser import extract_resume_text, parse_jd
from src.scoring.scorer import evaluate_candidate
from src.audit_logger import log_action, log_override, get_audit_log, get_overrides
from src.schemas import CandidateResult, HireRecommendation
from data.sample_data import SAMPLE_JD, SAMPLE_RESUMES
from src.llm_client import PROVIDER
import os


# ── Helpers ───────────────────────────────────────────────────────────────────
def score_color(score: float) -> str:
    if score >= 8:
        return "#155724"
    elif score >= 6.5:
        return "#004085"
    elif score >= 5:
        return "#856404"
    else:
        return "#721c24"


def score_bg(score: float) -> str:
    if score >= 8:
        return "#d4edda"
    elif score >= 6.5:
        return "#cce5ff"
    elif score >= 5:
        return "#fff3cd"
    else:
        return "#f8d7da"


def render_score_bar(label: str, score: float, weight: str, justification: str):
    bar_width = int(score * 10)
    color = "#ff6b35" if score >= 7 else ("#f0ad4e" if score >= 5 else "#dc3545")
    st.markdown(f"""
    <div style="margin: 8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
            <span style="font-size:0.85rem; font-weight:500;">{label}</span>
            <span style="font-size:0.8rem; color:var(--muted);">{weight} · <b style="color:{color}">{score}/10</b></span>
        </div>
        <div class="progress-bar-bg">
            <div style="width:{bar_width}%; background:{color}; height:100%; border-radius:4px; transition:width 0.5s;"></div>
        </div>
        <div style="font-size:0.75rem; color:var(--muted); margin-top:2px;">{justification}</div>
    </div>
    """, unsafe_allow_html=True)


def recommendation_badge(rec: HireRecommendation) -> str:
    badges = {
        HireRecommendation.STRONG_YES: ("🟢 Strong Yes", "score-strong-yes"),
        HireRecommendation.YES: ("🔵 Yes", "score-yes"),
        HireRecommendation.MAYBE: ("🟡 Maybe", "score-maybe"),
        HireRecommendation.NO: ("🔴 No", "score-no"),
        HireRecommendation.STRONG_NO: ("⛔ Strong No", "score-no"),
    }
    label, css = badges.get(rec, ("Unknown", "score-no"))
    return f'<span class="score-badge {css}">{label}</span>'


# ── Session State ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = []
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "processing" not in st.session_state:
    st.session_state.processing = False

# Auto-run sample analysis in dev mode when using MOCK provider.
try:
    auto = os.getenv("AUTO_RUN_SAMPLES", "").lower() in ("1", "true", "yes")
except Exception:
    auto = False

if PROVIDER == "mock" and auto and not st.session_state.results:
    # Quick headless run to populate the UI for demo/dev purposes
    try:
        jd = parse_jd(SAMPLE_JD)
        results = []
        for name, text in SAMPLE_RESUMES.items():
            res = evaluate_candidate(text, name, jd)
            results.append(res)
        results.sort(key=lambda r: r.final_score, reverse=True)
        st.session_state.results = results
        st.session_state.jd_text = SAMPLE_JD
        # Also write a simple JSON summary for validation purposes
        try:
            import json as _json
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
                _json.dump(out, fh, ensure_ascii=False, indent=2)
        except Exception as _e:
            print(f"⚠️  Failed to write auto_run_results.json: {_e}")
    except Exception as e:
        print(f"⚠️ AUTO_RUN_SAMPLES failed: {e}")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🔍 TalentLens</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.8rem; color:var(--muted);">AI Recruitment Intelligence</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**Navigation**")
    page = st.radio(
        "",
        ["🏠 Upload & Analyze", "📊 Shortlist Report", "🔍 Bias Audit", "💬 Interview Kit", "🛡️ Audit Trail"],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Quick Stats**")
    n = len(st.session_state.results)
    if n > 0:
        shortlisted = sum(1 for r in st.session_state.results
                          if r.hire_recommendation in [HireRecommendation.STRONG_YES, HireRecommendation.YES])
        flagged = sum(1 for r in st.session_state.results if r.bias_audit.bias_flag)
        st.markdown(f"- **{n}** candidates analyzed")
        st.markdown(f"- **{shortlisted}** shortlisted")
        st.markdown(f"- **{flagged}** bias flags ⚠️")
    else:
        st.markdown("*No data yet*")

    st.divider()
    st.markdown("""
    <div style="font-size:0.75rem; color:var(--muted);">
    <b>Innovations</b><br>
    🧠 Blind Bias Audit<br>
    💬 Targeted Interview Qs<br>
    🔬 Personality Signals<br>
    ✅ Pydantic Validated Scores<br>
    📋 Full Audit Trail
    </div>
    """, unsafe_allow_html=True)


# ── Page: Upload & Analyze ────────────────────────────────────────────────────
if "Upload" in page:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="main-header">TalentLens AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="tagline">Resume Intelligence · Bias Auditing · Interview Generation</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.results:
            st.success(f"✅ {len(st.session_state.results)} candidates ready")

    st.markdown("<br>", unsafe_allow_html=True)

    # JD Input
    st.markdown('<div class="section-title">Step 1 — Job Description</div>', unsafe_allow_html=True)
    use_sample_jd = st.toggle("Use sample JD (Senior Backend Engineer)", value=False)

    jd_input = st.text_area(
        "Paste your Job Description here",
        value=SAMPLE_JD if use_sample_jd else st.session_state.jd_text,
        height=200,
        placeholder="Paste the full job description including required skills, experience, education requirements...",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Resume Input
    st.markdown('<div class="section-title">Step 2 — Candidate Resumes</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Input method",
        ["📁 Upload Files (PDF/DOCX/TXT)", "📝 Use Sample Resumes"],
        horizontal=True,
    )

    uploaded_resumes = {}

    if "Upload Files" in input_mode:
        uploaded_files = st.file_uploader(
            "Upload resumes",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            for f in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
                    tmp.write(f.read())
                    uploaded_resumes[f.name] = ("__FILE__", tmp.name)
            st.info(f"📎 {len(uploaded_files)} resume(s) uploaded")
    else:
        selected = st.multiselect(
            "Select sample candidates",
            list(SAMPLE_RESUMES.keys()),
            default=list(SAMPLE_RESUMES.keys()),
        )
        for name in selected:
            uploaded_resumes[name] = ("__SAMPLE__", name)  # tuple flag: (type, key)

    st.markdown("<br>", unsafe_allow_html=True)

    # Run Analysis
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_btn = st.button(
            "🚀 Run Analysis",
            type="primary",
            disabled=not jd_input or not uploaded_resumes,
            use_container_width=True,
        )

    with col_info:
        st.markdown("""
        <div style="font-size:0.8rem; color:var(--muted); padding-top:10px;">
        Analysis includes: Rubric scoring · Bias audit · Interview questions · Personality signals<br>
        <i>Approx 15-20 seconds per candidate (API calls)</i>
        </div>
        """, unsafe_allow_html=True)

    if run_btn and jd_input and uploaded_resumes:
        st.session_state.results = []
        log_action("ANALYSIS_STARTED", details={"jd_length": len(jd_input), "candidates": len(uploaded_resumes)})

        with st.spinner("Parsing Job Description..."):
            jd = parse_jd(jd_input)
            st.session_state.jd_text = jd_input

        st.success(f"✅ JD parsed: **{jd.role_title}** · {jd.seniority_level} · {jd.domain}")
        st.markdown("<br>", unsafe_allow_html=True)

        progress = st.progress(0)
        status_box = st.empty()
        results = []

        for i, (filename, filepath) in enumerate(uploaded_resumes.items()):
            status_box.markdown(f"⏳ Analyzing **{filename}** ({i+1}/{len(uploaded_resumes)})...")
            tmp_path = None
            try:
                # Handle sample resumes (stored as tuple) vs uploaded files (stored as path string)
                if isinstance(filepath, tuple) and filepath[0] == "__SAMPLE__":
                    resume_text = SAMPLE_RESUMES[filepath[1]]
                else:
                    tmp_path = filepath[1] if isinstance(filepath, tuple) else filepath
                    resume_text = extract_resume_text(tmp_path)

                if not resume_text or len(resume_text.strip()) < 50:
                    status_box.markdown(f"⚠️ Skipping **{filename}** — file appears empty or unreadable.")
                    progress.progress((i + 1) / len(uploaded_resumes))
                    continue

                result = evaluate_candidate(resume_text, filename, jd)
                results.append(result)
                log_action("CANDIDATE_SCORED", result.candidate_name, {
                    "score": result.weighted_total,
                    "recommendation": result.hire_recommendation.value,
                    "bias_flag": result.bias_audit.bias_flag,
                })
                status_box.markdown(f"✅ **{result.candidate_name}** — {result.weighted_total}/10 · {result.hire_recommendation.value}")

            except Exception as e:
                import traceback
                err_detail = traceback.format_exc()
                status_box.markdown(f"❌ Error on **{filename}**: {str(e)[:200]}")
                print(f"Full error for {filename}:\n{err_detail}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            progress.progress((i + 1) / len(uploaded_resumes))
            time.sleep(0.1)

        # Sort by final score
        results.sort(key=lambda r: r.final_score, reverse=True)
        st.session_state.results = results
        status_box.empty()
        progress.empty()

        st.success(f"🎉 Analysis complete! {len(results)} candidates evaluated. View results in **Shortlist Report**.")
        log_action("ANALYSIS_COMPLETE", details={"total_candidates": len(results)})


# ── Page: Shortlist Report ────────────────────────────────────────────────────
elif "Report" in page:
    st.markdown('<div class="main-header" style="font-size:2rem;">Shortlist Report</div>', unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("👆 Run an analysis first from the Upload & Analyze page.")
        st.stop()

    results = st.session_state.results

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-num">{len(results)}</div>
        <div class="metric-label">Total Evaluated</div></div>""", unsafe_allow_html=True)
    shortlisted_n = sum(1 for r in results if r.hire_recommendation in [HireRecommendation.STRONG_YES, HireRecommendation.YES])
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-num">{shortlisted_n}</div>
        <div class="metric-label">Shortlisted</div></div>""", unsafe_allow_html=True)
    flagged_n = sum(1 for r in results if r.bias_audit.bias_flag)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-num">{flagged_n}</div>
        <div class="metric-label">Bias Flags</div></div>""", unsafe_allow_html=True)
    avg = round(sum(r.final_score for r in results) / len(results), 1) if results else 0
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="metric-num">{avg}</div>
        <div class="metric-label">Avg Score</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Candidate cards
    for i, result in enumerate(results):
        rank_class = f"rank-{i+1}" if i < 3 else "rank-other"
        rank_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        bias_class = f"bias-{result.bias_audit.fairness_index.lower()}"

        with st.container():
            st.markdown(f"""
            <div class="candidate-card {rank_class}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                    <div>
                        <span style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.2rem;">{rank_icon} {result.candidate_name}</span>
                        <span style="margin-left:8px; font-size:0.8rem; color:var(--muted);">{result.profile.current_role or 'N/A'} · {result.profile.years_experience}y exp</span>
                    </div>
                    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                        <span style="font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800; color:{score_color(result.final_score)};">{result.final_score}/10</span>
                        {recommendation_badge(result.hire_recommendation)}
                        <span class="{bias_class}">Fairness: {result.bias_audit.fairness_index}</span>
                    </div>
                </div>
                <div style="margin-top:12px; font-size:0.9rem; color:#ccc; line-height:1.5;">{result.executive_summary}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📋 Full breakdown — {result.candidate_name}"):
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 Scores", "🧠 Bias Audit", "💬 Interview Qs", "🔬 Personality", "✏️ HR Override"
                ])

                with tab1:
                    col_s, col_d = st.columns([1, 1])
                    with col_s:
                        st.markdown('<div class="section-title">Rubric Scores</div>', unsafe_allow_html=True)
                        render_score_bar("Skills Match", result.scores.skills_match.score, "30%",
                                         result.scores.skills_match.justification)
                        render_score_bar("Experience Relevance", result.scores.experience_relevance.score, "25%",
                                         result.scores.experience_relevance.justification)
                        render_score_bar("Education & Certs", result.scores.education_certs.score, "15%",
                                         result.scores.education_certs.justification)
                        render_score_bar("Project / Portfolio", result.scores.project_portfolio.score, "20%",
                                         result.scores.project_portfolio.justification)
                        render_score_bar("Communication Quality", result.scores.communication_quality.score, "10%",
                                         result.scores.communication_quality.justification)
                    with col_d:
                        col_str, col_con = st.columns(2)
                        with col_str:
                            st.markdown('<div class="section-title">Strengths</div>', unsafe_allow_html=True)
                            for s in result.strengths:
                                st.markdown(f"✅ {s}")
                        with col_con:
                            st.markdown('<div class="section-title">Concerns</div>', unsafe_allow_html=True)
                            for c in result.concerns:
                                st.markdown(f"⚠️ {c}")

                        st.markdown('<div class="section-title" style="margin-top:16px;">Skills</div>', unsafe_allow_html=True)
                        skills_html = " ".join([
                            f'<span style="background:#2c2c2c;color:#ff6b35;padding:3px 8px;border-radius:4px;font-size:0.8rem;margin:2px;display:inline-block;border:1px solid #444;">{s}</span>'
                            for s in result.profile.skills[:12]
                        ])
                        st.markdown(skills_html, unsafe_allow_html=True)

                with tab2:
                    st.markdown(f'<span class="innovation-tag">Innovation 1</span> <b>Blind vs Normal Score Comparison</b>', unsafe_allow_html=True)
                    ba = result.bias_audit
                    col_n, col_b, col_d = st.columns(3)
                    with col_n:
                        st.metric("Normal Score", f"{ba.normal_score}/10")
                    with col_b:
                        st.metric("Blind Score", f"{ba.blind_score}/10")
                    with col_d:
                        st.metric("Drift", f"{ba.score_drift} pts", f"{ba.drift_percentage}%",
                                  delta_color="inverse" if ba.bias_flag else "normal")

                    if ba.bias_flag:
                        st.error(f"⚠️ **Bias Flag Raised** — {ba.auditor_note}")
                    else:
                        st.success(f"✅ {ba.auditor_note}")

                    if ba.bias_signals_detected:
                        st.markdown("**Signals detected in resume:**")
                        for sig in ba.bias_signals_detected:
                            st.markdown(f"• {sig}")
                    else:
                        st.markdown("*No obvious bias signals detected in text.*")

                with tab3:
                    st.markdown(f'<span class="innovation-tag">Innovation 2</span> <b>Targeted Interview Questions</b>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    for j, q in enumerate(result.interview_questions):
                        st.markdown(f"""
                        <div class="q-card">
                            <div style="font-weight:600; margin-bottom:6px;">Q{j+1}: {q.question}</div>
                            <div style="font-size:0.8rem; color:var(--muted); margin-bottom:4px;">
                                🎯 Targeting: <b>{q.dimension_targeted}</b> · {q.why_this_question}
                            </div>
                            <div style="display:flex; gap:16px; margin-top:8px; font-size:0.8rem;">
                                <div><span style="color:#155724;">✅ Good answer:</span> {q.green_flag_answer}</div>
                                <div><span style="color:#721c24;">🚩 Red flag:</span> {q.red_flag_answer}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                with tab4:
                    st.markdown(f'<span class="innovation-tag">Innovation 3</span> <b>Writing-Style Personality Signals</b>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    for pi in result.personality_insights:
                        conf_color = {"High": "#155724", "Medium": "#856404", "Low": "#721c24"}.get(pi.confidence, "#000")
                        st.markdown(f"""
                        <div style="display:flex; gap:12px; align-items:flex-start; margin:10px 0; padding:12px; background:#f8f7f4; border-radius:8px;">
                            <div style="min-width:120px; font-weight:600;">{pi.trait}</div>
                            <div style="flex:1; font-size:0.9rem;">{pi.signal}</div>
                            <div style="min-width:60px; text-align:right; font-size:0.8rem; font-weight:600; color:{conf_color};">{pi.confidence}</div>
                        </div>
                        """, unsafe_allow_html=True)

                with tab5:
                    st.markdown("**HR Override** — Adjust score with a documented reason")
                    hr_name = st.text_input("Your name", key=f"hr_name_{i}", placeholder="e.g. Prachi Mehra")
                    override_score = st.slider(
                        "Override score",
                        0.0, 10.0,
                        float(result.hr_override_score or result.weighted_total),
                        0.5,
                        key=f"override_{i}",
                    )
                    override_reason = st.text_area(
                        "Reason for override (mandatory)",
                        key=f"reason_{i}",
                        placeholder="e.g. Candidate has referral from VP Engineering; adjusting score upward.",
                    )
                    if st.button("💾 Save Override", key=f"save_{i}"):
                        if not hr_name or not override_reason:
                            st.error("Both your name and a reason are required.")
                        else:
                            result.hr_override_score = override_score
                            result.hr_override_reason = override_reason
                            result.hr_override_by = hr_name
                            log_override(result.candidate_name, result.weighted_total, override_score, override_reason, hr_name)
                            st.success(f"✅ Override saved. New score: {override_score}/10")
                            st.rerun()

                    if result.hr_override_score:
                        st.info(f"🔄 Currently overridden to **{result.hr_override_score}/10** by {result.hr_override_by}: *{result.hr_override_reason}*")

        st.markdown("")  # spacing


# ── Page: Bias Audit ─────────────────────────────────────────────────────────
elif "Bias" in page:
    st.markdown('<div class="main-header" style="font-size:2rem;">Bias Audit Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<span class="innovation-tag">Innovation 1</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("Run an analysis first.")
        st.stop()

    st.markdown("""
    **How this works:** Each resume is scored twice — once normally and once with names,
    gender pronouns, and prestige institution names removed. A drift >10% triggers a bias flag,
    surfacing where evaluator perception (or the LLM) may be influenced by non-merit signals.
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    for result in st.session_state.results:
        ba = result.bias_audit
        flag_icon = "⚠️" if ba.bias_flag else "✅"
        # Darker colors for better contrast
        color_map = {"GREEN": "#1e7e34", "YELLOW": "#997404", "RED": "#842029"}
        text_color = {"GREEN": "#ffffff", "YELLOW": "#ffffff", "RED": "#ffffff"}
        bg_color = color_map[ba.fairness_index]
        txt_color = text_color[ba.fairness_index]

        st.markdown(f"""
        <div style="background:{bg_color}; color:{txt_color}; border-radius:12px; padding:16px; margin:8px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b>{flag_icon} {result.candidate_name}</b>
                <div>
                    Normal: <b>{ba.normal_score}/10</b> →
                    Blind: <b>{ba.blind_score}/10</b> |
                    Drift: <b>{ba.drift_percentage}%</b> |
                    Fairness: <b>{ba.fairness_index}</b>
                </div>
            </div>
            <div style="font-size:0.85rem; margin-top:6px; color:{txt_color};">{ba.auditor_note}</div>
            {"<div style='font-size:0.8rem; margin-top:4px; color:" + txt_color + ";'>Signals: " + ", ".join(ba.bias_signals_detected) + "</div>" if ba.bias_signals_detected else ""}
        </div>
        """, unsafe_allow_html=True)


# ── Page: Interview Kit ───────────────────────────────────────────────────────
elif "Interview" in page:
    st.markdown('<div class="main-header" style="font-size:2rem;">Interview Kit</div>', unsafe_allow_html=True)
    st.markdown('<span class="innovation-tag">Innovation 2</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.results:
        st.info("Run an analysis first.")
        st.stop()

    shortlisted = [r for r in st.session_state.results
                   if r.hire_recommendation in [HireRecommendation.STRONG_YES, HireRecommendation.YES]]

    if not shortlisted:
        st.warning("No shortlisted candidates yet.")
        st.stop()

    selected_name = st.selectbox("Select candidate", [r.candidate_name for r in shortlisted])
    result = next(r for r in shortlisted if r.candidate_name == selected_name)

    st.markdown(f"### Interview Guide — {result.candidate_name}")
    st.markdown(f"Score: **{result.final_score}/10** · {result.hire_recommendation.value}")
    st.markdown(f"*{result.executive_summary}*")
    st.divider()

    st.markdown("**Questions are generated based on this candidate's specific weak points and resume gaps.**")
    st.markdown("<br>", unsafe_allow_html=True)

    for j, q in enumerate(result.interview_questions):
        with st.expander(f"Q{j+1}: {q.question[:80]}...", expanded=True):
            st.markdown(f"**Full question:** {q.question}")
            st.markdown(f"**Why ask this:** {q.why_this_question}")
            col_g, col_r = st.columns(2)
            with col_g:
                st.success(f"✅ **Green flag answer:** {q.green_flag_answer}")
            with col_r:
                st.error(f"🚩 **Red flag answer:** {q.red_flag_answer}")

    st.divider()
    st.markdown("**Personality Signals to watch during interview:**")
    for pi in result.personality_insights:
        st.markdown(f"• **{pi.trait}** ({pi.confidence} confidence) — {pi.signal}")


# ── Page: Audit Trail ─────────────────────────────────────────────────────────
elif "Audit" in page:
    st.markdown('<div class="main-header" style="font-size:2rem;">Audit Trail</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**System Actions Log**")
        logs = get_audit_log()
        if logs:
            for log in logs[:20]:
                details = json.loads(log["details"]) if log["details"] else {}
                st.markdown(f"""
                <div style="border:1px solid #2c2c2c;border-radius:8px;padding:10px;margin:6px 0;font-size:0.82rem;background:#1a1a1a;color:#e8e4d9;">
                    <div style="display:flex;justify-content:space-between;">
                        <b>{log['action']}</b>
                        <span style="color:#888;">{log['timestamp'][:16]}</span>
                    </div>
                    {f"<div>Candidate: {log['candidate_name']}</div>" if log['candidate_name'] else ""}
                    <div style="color:#999;">{str(details)[:120]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No logs yet.")

    with col_b:
        st.markdown("**HR Override Log**")
        overrides = get_overrides()
        if overrides:
            for ov in overrides:
                st.markdown(f"""
                <div style="border:1px solid #ffc107;border-radius:8px;padding:10px;margin:6px 0;font-size:0.82rem;background:#d4a574;color:#0f0e17;">
                    <b>{ov['candidate_name']}</b> — overridden by <b>{ov['hr_name']}</b><br>
                    {ov['original_score']} → {ov['override_score']}/10<br>
                    <i>"{ov['reason']}"</i><br>
                    <span style="color:#2c2c2c;font-weight:500;">{ov['timestamp'][:16]}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No overrides recorded yet.")
