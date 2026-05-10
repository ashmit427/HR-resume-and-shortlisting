# 🔍 TalentLens AI — HR Resume Shortlisting Agent

> **Unique differentiators:** Blind Bias Auditing · Auto Interview Question Generation · Personality Signal Extraction · Full Audit Trail · Pydantic-Validated Scoring

---

## 📌 Problem Statement

HR teams screen 200–500+ resumes per role, leading to:
- Evaluation fatigue → inconsistent scoring
- Unconscious bias → prestige/name/gender influencing decisions
- Generic shortlist reports → interviewers still unprepared
- No audit trail → no accountability for hiring decisions

**TalentLens** solves all four.

---

## 🚀 What Makes This Different (vs 250 Other Submissions)

| Feature | Standard Submission | TalentLens |
|---|---|---|
| Scoring | LLM scores once | Scores TWICE (blind + normal) and diffs them |
| Bias Detection | None | Fairness Index with drift % per candidate |
| Interview Help | None | 3 targeted questions per candidate gap |
| Personality | None | Writing-style soft-skill inference |
| Output validation | String parsing | Pydantic v2 strict schemas |
| Audit | None | Full SQLite audit trail + override log |
| UI | Basic or none | 5-page Streamlit app with custom CSS |

---

## 🧠 Innovations

### Innovation 1 — Blind Bias Audit
Every resume is scored **twice**:
1. **Normal mode** — full text as-is
2. **Blind mode** — names, gender pronouns, prestige institution names stripped

If the weighted score **drifts >10%** between the two, a `⚠️ Bias Flag` is raised and the "Fairness Index" column shows RED. HR is notified to re-review manually. This is the only intern project in this cohort that proactively addresses AI fairness.

### Innovation 2 — Targeted Interview Question Generation
After scoring, the agent identifies each candidate's **bottom 3 dimensions** and generates **3 gap-filling interview questions** that:
- Reference the candidate's actual resume data (not generic)
- Specify what a green-flag vs red-flag answer looks like
- Map directly to the hiring rubric

This turns TalentLens from a passive filter into an **active hiring co-pilot**.

### Innovation 3 — Writing-Style Personality Signal Extraction
The LLM analyzes **how** the candidate writes (verb choice, quantification habits, active vs passive voice) to infer soft-skill signals like:
- Ownership Mindset
- Data-Driven thinking
- Collaboration signals

Crucially, this is based on **linguistic patterns only**, not demographics.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    TalentLens Agent                       │
│                                                          │
│  ┌─────────┐   ┌──────────┐   ┌──────────────────────┐  │
│  │ JD      │   │ Resume   │   │ Scoring Engine       │  │
│  │ Parser  │──▶│ Parser   │──▶│                      │  │
│  │ (Claude)│   │ (Claude) │   │  Normal Score        │  │
│  └─────────┘   └──────────┘   │  + Bias Audit        │  │
│                               │  + Interview Qs      │  │
│  ┌───────────────────────┐    │  + Personality       │  │
│  │ Pydantic v2 Schemas   │◀───│                      │  │
│  │ (output validation)   │    └──────────────────────┘  │
│  └───────────────────────┘                              │
│                                                          │
│  ┌─────────────────┐   ┌──────────────────────────────┐  │
│  │  SQLite Audit   │   │  Streamlit UI (5 pages)      │  │
│  │  Trail Logger   │   │  - Upload & Analyze          │  │
│  │  + HR Override  │   │  - Shortlist Report          │  │
│  │  Log            │   │  - Bias Audit Dashboard      │  │
│  └─────────────────┘   │  - Interview Kit             │  │
│                         │  - Audit Trail               │  │
│                         └──────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**Agent Flow:**
```
Input (JD + Resumes)
  → Parse JD (Claude: extract structured requirements)
  → Parse Resume (Claude: extract structured profile)
  → Score Normal (Claude: 5-dimension rubric, Pydantic validated)
  → Score Blind (Claude: anonymized text, same rubric)
  → Bias Diff (drift %, fairness flag)
  → Generate Interview Questions (Claude: gap-targeted)
  → Generate Personality Signals (Claude: writing-style analysis)
  → Rank (by weighted total / HR override score)
  → Report (Streamlit UI + audit log)
  → HR Override (logged with reason + reviewer name)
```

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|---|---|---|
| **LLM** | Claude claude-sonnet-4-20250514 (Anthropic) | Best structured output, 200K context, tool-calling, fastest in class |
| **Output Validation** | Pydantic v2 | Prevents hallucinated scores — strict typing with `field_validator` |
| **Resume Parse** | PyMuPDF + python-docx + Claude | Handles PDF/DOCX/TXT; LLM handles unstructured layouts |
| **UI** | Streamlit | Rapid deployment; custom CSS for production feel |
| **Audit Storage** | SQLite | Lightweight, no infra needed, persistent |
| **Observability** | LangSmith (optional) | Trace every LLM call for debugging |
| **Env management** | python-dotenv | API keys never in code |

---

## 🔒 Security Mitigations

| Risk | Mitigation |
|---|---|
| **Prompt Injection** | Input text is never concatenated into system prompts raw. All user content is placed in a clearly delimited `RESUME:` block with structured JSON output schemas enforced |
| **PII / Data Privacy** | No candidate PII is logged in plaintext. Audit log stores only names + scores. In-memory processing only — no files persisted to cloud |
| **API Key Exposure** | `.env` + `python-dotenv`. `.env` in `.gitignore`. `.env.example` provided with no real keys. Never hardcoded |
| **Hallucination** | Pydantic v2 `BaseModel` with `ge=0 le=10` validators. If LLM returns invalid JSON, the error is caught and surfaced, not silently accepted |
| **Unauthorized Access** | In demo mode, no auth needed. In production: add `st.secrets` + OAuth via Streamlit Cloud or a FastAPI auth middleware |
| **Bias / Fairness** | Innovation 1 directly mitigates this. Blind scoring, fairness index, HR review requirement for flagged candidates |
| **HR Override Abuse** | Every override requires a named reviewer + written reason. Logged to immutable SQLite audit table with timestamp |

---

## ⚙️ Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/talentlens-ai
cd talentlens-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Run the application
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 📁 Project Structure

```
talentlens-ai/
├── app.py                      # Streamlit UI (5 pages)
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── schemas.py              # Pydantic v2 output schemas
│   ├── audit_logger.py         # SQLite audit trail
│   ├── parsers/
│   │   └── resume_parser.py    # PDF/DOCX/TXT extraction + JD parsing
│   └── scoring/
│       └── scorer.py           # All 3 innovations + scoring engine
└── data/
    ├── sample_data.py          # 5 sample resumes + JD for demo
    └── audit_trail.db          # Auto-created SQLite DB
```

---

## 🧪 Testing

Run with 5 sample candidates covering:
- ✅ Strong match (Priya Sharma, Meera Pillai, Ananya Krishnan)
- ⚠️ Partial match (Vikram Nair)
- ❌ No match (Rahul Verma)

Expected results test all rubric dimensions, bias flags, and interview question quality.

---

## 📝 Prompt Design

Key design decisions:
1. **Structured output first**: All prompts end with "Return ONLY valid JSON" — no preamble
2. **Anchored rubric**: Each dimension score includes explicit anchors (0-3 / 4-6 / 8-10) to reduce calibration variance
3. **Evidence required**: Every score requires a direct evidence quote from the resume
4. **Blind mode flag**: Bias audit uses `(BLIND MODE)` prefix so LLM knows context
5. **Gap-targeted questions**: Interview prompt explicitly passes the candidate's bottom 3 dimensions

---

## 📊 Sample Output

```
Rank 1: Ananya Krishnan — 8.4/10 | Strong Yes | Fairness: GREEN
Rank 2: Meera Pillai    — 8.1/10 | Strong Yes | Fairness: GREEN  
Rank 3: Priya Sharma    — 7.9/10 | Yes        | Fairness: YELLOW ⚠️
Rank 4: Vikram Nair     — 4.2/10 | No         | Fairness: GREEN
Rank 5: Rahul Verma     — 2.8/10 | Strong No  | Fairness: GREEN
```

---

## 🎓 Learnings & Future Work

- **LangSmith tracing**: Adding `LANGSMITH_API_KEY` enables full trace visualization
- **Caching**: `sqlitedict` can cache JD parses to reduce API cost during development
- **Multi-language resumes**: Claude handles Hindi/mixed resumes reasonably well
- **Future**: Add semantic embeddings (SentenceTransformers) for skills matching as a double-check on LLM scoring
