"""
Resume & JD Parser — with safe fallbacks to prevent 'Unknown Role' bug
Works with Anthropic OR HuggingFace via unified llm_client.
"""
import re
from pathlib import Path

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from src.llm_client import llm_json
from src.schemas import CandidateProfile, JDRequirements

BIAS_MARKERS = [
    r"\b(he|she|his|her|him|himself|herself)\b",
    r"\b(IIT|IIM|Harvard|Oxford|Cambridge|Stanford|MIT|Yale|Princeton)\b",
    r"\b(19|20)\d{2}\b",
    r"\baged?\s+\d+\b",
]


def extract_text_from_pdf(path: str) -> str:
    if not HAS_FITZ:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    doc = fitz.open(path)
    return "".join(page.get_text() for page in doc).strip()


def extract_text_from_docx(path: str) -> str:
    if not HAS_DOCX:
        raise ImportError("python-docx not installed. Run: pip install python-docx")
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_resume_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    elif suffix in [".docx", ".doc"]:
        return extract_text_from_docx(path)
    elif suffix in [".txt", ".md"]:
        return p.read_text(encoding="utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {p.suffix}. Use PDF, DOCX, or TXT.")


def anonymize_resume(text: str) -> str:
    lines = text.split("\n")
    out, done = [], False
    for line in lines:
        if line.strip() and not done:
            out.append("[CANDIDATE NAME REDACTED]")
            done = True
        else:
            out.append(line)
    anon = "\n".join(out)
    for pat in BIAS_MARKERS:
        anon = re.sub(pat, "[REDACTED]", anon, flags=re.IGNORECASE)
    for col in ["IIT","IIM","Harvard","Oxford","Cambridge","Stanford","MIT","Yale","Princeton","BITS","NIT"]:
        anon = anon.replace(col, "Premier Institute")
    return anon


def parse_jd(jd_text: str) -> JDRequirements:
    """Parse JD with safe fallback defaults so it never returns 'Unknown Role'."""
    prompt = f"""Extract information from this Job Description and return ONLY a JSON object.
No explanation. No markdown. Just the raw JSON.

JD TEXT:
{jd_text[:3000]}

Return exactly this JSON structure:
{{
  "role_title": "exact job title from the JD",
  "required_skills": ["skill1", "skill2", "skill3"],
  "preferred_skills": ["skill1", "skill2"],
  "min_experience_years": 4.0,
  "education_requirement": "B.Tech/BE in Computer Science or equivalent",
  "key_responsibilities": ["responsibility1", "responsibility2", "responsibility3"],
  "domain": "Software Engineering",
  "seniority_level": "Senior"
}}"""

    try:
        data = llm_json(prompt, max_tokens=1200)
        # Fill in safe defaults for any missing/empty fields
        if not data.get("role_title") or data["role_title"].lower() in ["unknown", "string", ""]:
            # Extract from first line of JD as fallback
            first_line = next((l.strip() for l in jd_text.split("\n") if l.strip()), "Software Engineer")
            data["role_title"] = first_line[:80]
        if not data.get("domain") or data["domain"].lower() in ["general", "string", ""]:
            data["domain"] = "Software Engineering"
        if not data.get("seniority_level") or data["seniority_level"].lower() in ["junior", "string", ""]:
            # Detect from JD text
            jd_lower = jd_text.lower()
            if "senior" in jd_lower:   data["seniority_level"] = "Senior"
            elif "lead" in jd_lower:    data["seniority_level"] = "Lead"
            elif "principal" in jd_lower: data["seniority_level"] = "Principal"
            elif "junior" in jd_lower:  data["seniority_level"] = "Junior"
            else:                        data["seniority_level"] = "Mid"
        if not data.get("required_skills"):
            data["required_skills"] = ["Python", "REST APIs", "SQL"]
        if not data.get("preferred_skills"):
            data["preferred_skills"] = []
        if not data.get("key_responsibilities"):
            data["key_responsibilities"] = ["Design and build backend systems"]
        if not data.get("min_experience_years"):
            data["min_experience_years"] = 3.0
        if not data.get("education_requirement"):
            data["education_requirement"] = "Bachelor's degree in Computer Science or equivalent"
        return JDRequirements(**data)
    except Exception as e:
        # Hard fallback — extract basics from raw JD text
        print(f"⚠️  JD parse error: {e} — using text extraction fallback")
        lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
        return JDRequirements(
            role_title=lines[0][:80] if lines else "Software Engineer",
            required_skills=["Python", "REST APIs", "SQL", "Docker"],
            preferred_skills=["AWS", "Kubernetes"],
            min_experience_years=3.0,
            education_requirement="Bachelor's in Computer Science or equivalent",
            key_responsibilities=["Build and maintain backend systems"],
            domain="Software Engineering",
            seniority_level="Senior" if "senior" in jd_text.lower() else "Mid",
        )


def parse_candidate_profile(resume_text: str) -> CandidateProfile:
    """Parse resume with safe fallback defaults."""
    prompt = f"""Extract structured data from this resume. Return ONLY JSON, no explanation, no markdown.

RESUME:
{resume_text[:4000]}

Return exactly this JSON:
{{
  "name": "candidate full name",
  "email": "email address or null",
  "phone": "phone number or null",
  "years_experience": 3.0,
  "current_role": "current job title or null",
  "skills": ["skill1", "skill2", "skill3"],
  "education": ["Degree, University, Year"],
  "certifications": ["certification name"],
  "projects": ["project description"],
  "summary_text": "2-3 sentence professional summary"
}}"""

    try:
        data = llm_json(prompt, max_tokens=1200)
        # Safe defaults
        if not data.get("name") or data["name"].lower() in ["string", "candidate", ""]:
            first_line = next((l.strip() for l in resume_text.split("\n") if l.strip()), "Unknown Candidate")
            data["name"] = first_line[:50]
        if not data.get("skills"):
            data["skills"] = ["Not specified"]
        if not data.get("education"):
            data["education"] = ["Not specified"]
        if not data.get("certifications"):
            data["certifications"] = []
        if not data.get("projects"):
            data["projects"] = []
        if not data.get("summary_text"):
            data["summary_text"] = "No summary available."
        if not data.get("years_experience"):
            data["years_experience"] = 0.0
        return CandidateProfile(**data)
    except Exception as e:
        print(f"⚠️  Resume parse error: {e} — using fallback")
        first_line = next((l.strip() for l in resume_text.split("\n") if l.strip()), "Unknown")
        return CandidateProfile(
            name=first_line[:50],
            email=None, phone=None,
            years_experience=0.0,
            current_role=None,
            skills=["Not parsed"],
            education=["Not parsed"],
            certifications=[],
            projects=[],
            summary_text="Could not parse resume automatically.",
        )
