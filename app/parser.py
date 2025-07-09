import re
from app.utils import SKILL_KEYWORDS, EDUCATION_KEYWORDS
import spacy
nlp = spacy.load("en_core_web_sm")

# ---------------- Name Extraction ----------------
def extract_name(text: str):
    top = [line.strip() for line in text.splitlines() if line.strip()][:10]
    for line in top:
        if any(x in line for x in (":", "/", "http", "@", "+")):
            continue
        if re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+){1,3}", line):
            return line.title()
    return None

# ---------------- Social Profiles ----------------
def extract_linkedin(text: str):
    """
    Returns the first LinkedIn profile URL it finds, e.g.
    https://www.linkedin.com/in/your‑profile
    """
    m = re.search(r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9_\-\/]+", text, re.I)
    return m.group(0) if m else None


def extract_github(text: str):
    """
    Returns the first GitHub profile URL it finds, e.g.
    https://github.com/your‑username
    """
    m = re.search(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_\-]+", text, re.I)
    return m.group(0) if m else None

# ---------------- Summary ----------------
def extract_summary(text: str):
    lines = text.splitlines()
    capture, buff = False, []
    for line in lines:
        if "summary" in line.lower():
            capture = True
            continue
        if capture:
            clean = line.strip()
            if not clean or (clean.isupper() and len(clean.split()) <= 3):
                break
            buff.append(clean)
    return " ".join(buff).strip() if buff else None

# ---------------- Skills ----------------
def extract_skills(text: str):
    lines = text.splitlines()
    capture = False
    found_skills = set()

    for line in lines:
        lower_line = line.lower()
        if "skills" in lower_line or "technical skills" in lower_line:
            capture = True
            continue
        if capture:
            # Stop if we hit another section header
            if line.strip().isupper() and len(line.strip().split()) <= 3:
                break

            # Extract all comma-separated tokens
            tokens = [token.strip().lower() for token in re.split(r"[:,]|,", line) if token.strip()]

            for token in tokens:
                for skill in SKILL_KEYWORDS:
                    if token == skill.lower():
                        found_skills.add(skill)

    return sorted(found_skills)

# ---------------- Education ----------------
def extract_education(text: str):
    lines = text.splitlines()
    education = []
    capture = False

    for line in lines:
        clean = line.strip()
        if "education" in clean.lower():
            capture = True
            continue
        if capture:
            # Stop when a new section starts (like PROJECTS, SKILLS, etc.)
            if clean.isupper() and len(clean.split()) <= 3:
                break
            # Only include lines with dates or known education keywords
            if re.search(r"\d{4}", clean) or any(k in clean.lower() for k in EDUCATION_KEYWORDS):
                education.append(clean)

    return education

# ---------------- Projects ----------------
TECH_MAP = {
    "react": "React.js", "node": "Node.js", "express": "Express.js", "mongodb": "MongoDB",
    "html": "HTML", "css": "CSS", "javascript": "JavaScript", "bootstrap": "Bootstrap",
    "passport": "Passport.js", "sql": "SQL", "python": "Python", "streamlit": "Streamlit",
    "googletrans": "googletrans", "gtts": "gTTS", "speechrecognition": "speech_recognition"
}
TECH_KEYS = list(TECH_MAP)

def extract_projects(text: str):
    lines = text.splitlines()
    capture = False
    projects, title, desc = [], "", []
    month_re = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}"

    for line in lines:
        if "projects" in line.lower():
            capture = True
            continue
        if not capture:
            continue
        if line.strip().isupper() and len(line.strip().split()) <= 3 and "projects" not in line.lower():
            break
        if re.search(month_re, line):
            if title and desc:
                txt = " ".join(desc)
                techs = sorted({TECH_MAP[k] for k in TECH_KEYS if k in txt.lower()})
                projects.append({"title": title, "description": txt, "technologies": techs})
                desc = []
            title = line.strip()
        else:
            if line.strip():
                desc.append(line.strip())

    if title and desc:
        txt = " ".join(desc)
        techs = sorted({TECH_MAP[k] for k in txt.lower() for k in TECH_KEYS if k in txt.lower()})
        projects.append({"title": title, "description": txt, "technologies": techs})

    return projects

# ---------------- ATS Scoring ----------------
def score_resume(parsed: dict):
    """
    Returns a breakdown dict and total score out of 100.
    """
    score = 0
    breakdown = {}

    # 1. Contact Info (email + phone) – 20 pts
    has_email = bool(parsed.get("email"))
    has_phone = bool(parsed.get("phone"))
    breakdown["Contact Info"] = 20 if (has_email and has_phone) else 10 if (has_email or has_phone) else 0
    score += breakdown["Contact Info"]

    # 2. Social Links (LinkedIn + GitHub) – 10 pts
    has_linkedin = bool(parsed.get("linkedin"))
    has_github = bool(parsed.get("github"))
    breakdown["Social Links"] = 10 if (has_linkedin and has_github) else 5 if (has_linkedin or has_github) else 0
    score += breakdown["Social Links"]

    # 3. Skills – 15 pts (≥ 5 skills → 15 pts, 1–4 skills → 10 pts)
    skills_cnt = len(parsed.get("skills", []))
    breakdown["Skills"] = 15 if skills_cnt >= 5 else 10 if skills_cnt else 0
    score += breakdown["Skills"]

    # 4. Projects – 15 pts (≥ 2 projects → 15 pts, 1 project → 10 pts)
    proj_cnt = len(parsed.get("projects", []))
    breakdown["Projects"] = 15 if proj_cnt >= 2 else 10 if proj_cnt == 1 else 0
    score += breakdown["Projects"]

    # 5. Education – 10 pts (≥ 1 entry → 10 pts)
    edu_cnt = len(parsed.get("education", [])) // 2      # 2 lines = 1 entry
    breakdown["Education"] = 10 if edu_cnt else 0
    score += breakdown["Education"]

    # 6. Work Experience – 15 pts (placeholder: zero until you implement extraction)
    experience_found = False           # TODO: hook up later
    breakdown["Work Experience"] = 15 if experience_found else 0
    score += breakdown["Work Experience"]

    # 7. Summary – 15 pts
    breakdown["Summary"] = 15 if parsed.get("summary") else 0
    score += breakdown["Summary"]

    breakdown["Total Score"] = score
    return breakdown

# ---------------- Master Parser ----------------
def parse_resume(text: str):
    doc = nlp(text)

    return {
        "name": extract_name(text),
        "phone": next(iter(re.findall(r"\+?\d[\d\s\-]{8,}\d", text)), None),  # ← fixed regex
        "email": next((t.text for t in doc if t.like_email), None),
        "linkedin": extract_linkedin(text),      # ← NEW
        "github": extract_github(text),          # ← NEW
        "summary": extract_summary(text),
        "skills": extract_skills(text),
        "projects": extract_projects(text),
        "education": extract_education(text),
    }

