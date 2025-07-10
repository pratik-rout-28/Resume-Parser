import os
import json
import base64
import pandas as pd
import streamlit as st
import plotly.express as px
from app.extractor import extract_text_from_pdf
from app.parser import parse_resume, score_resume
from app.exporter import export_resume
from app.utils import SKILL_CATEGORIES

# ---------- Page Config ----------
st.set_page_config(page_title="Smart Resume Checker", layout="wide")

# ---------- Custom CSS: Google Fonts + Animations ----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
<style>
body, .stApp {
    font-family: 'Poppins', sans-serif;
    background-color:#0e0e11;
    color:#FEFEFA;
}
.block-container { padding:2rem; }
.main-title {
    font-size:2.5rem;
    font-weight:700;
    color:#C1D7F0;
    margin-bottom:0.2rem;
}
.subtext {
    font-size:1rem;
    color:#FEFEFA;
    margin-bottom:2rem;
}
.stDownloadButton > button {
    border-radius:6px;
    padding:8px 16px;
    background-color:#1976D2;
    color:white;
    font-weight:600;
    margin-top: 1rem;
}
.fade-in {
    animation: fadeIn 1.5s ease-in;
}
.score-highlight {
    font-size: 1.8rem;
    font-weight: 600;
    color: #90CAF9;
    margin-top: 0.5rem;
}
@keyframes fadeIn {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.markdown('<div class="main-title">📝 Smart Resume Checker</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">Get instant feedback on your resume with suggestions and tips to make it better.</div>', unsafe_allow_html=True)

# ---------- File Upload ----------
uploaded_file = st.file_uploader("📄 Upload your resume (PDF only)", type=["pdf"])

if uploaded_file:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > 2:
        st.error("❌ Your file is too big. Please upload a PDF smaller than 2 MB.")
    else:
        progress = st.progress(0, text="⏳ Analyzing your resume...")

        # Step 1 – Save
        os.makedirs("resumes", exist_ok=True)
        resume_path = os.path.join("resumes", uploaded_file.name)
        with open(resume_path, "wb") as f:
            f.write(uploaded_file.read())
        progress.progress(25, text="📥 File uploaded.")

        # Step 2 – Extract
        raw_text = extract_text_from_pdf(resume_path)
        progress.progress(50, text="🔍 Reading your resume...")

        # Step 3 – Parse
        parsed = parse_resume(raw_text)
        score_breakdown = score_resume(parsed)
        progress.progress(75, text="🧠 Understanding your details...")

        # Step 4 – Export
        os.makedirs("output", exist_ok=True)
        json_path = "output/parsed_resume.json"
        pdf_path = "output/parsed_resume.pdf"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=4)
        export_resume(json_path, pdf_path)
        progress.progress(100, text="✅ All done!")

        st.success("✅ Your resume is ready!")

        # ---------- Report Columns ----------
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.subheader("📊 Resume Score & Insights")
            st.markdown(f"<span class='score-highlight fade-in'>⭐ Overall Score: {score_breakdown['Total Score']} / 100</span>", unsafe_allow_html=True)

            # Friendly tips
            suggestions = {
                "Contact Info": "Add both email and phone number so employers can reach you.",
                "Social Links": "Include LinkedIn and GitHub to show your online presence.",
                "Skills": "List at least 5 relevant technical skills that reflect your strengths.",
                "Projects": "Add 2+ projects with tools you used and what they achieved.",
                "Education": "Mention both school and college education clearly.",
                "Work Experience": "Mention internships, jobs, or freelance work if any.",
                "Summary": "Write a short intro about who you are and your goals."
            }

            max_points = {
                "Contact Info": 20, "Social Links": 10, "Skills": 15, "Projects": 15,
                "Education": 10, "Work Experience": 15, "Summary": 15
            }

            for section, pts in score_breakdown.items():
                if section == "Total Score":
                    continue
                emoji = "✅" if pts == max_points[section] else "⚠️" if pts > 0 else "❌"
                st.markdown(f"**{emoji} {section}**")
                if pts < max_points[section]:
                    with st.expander("📌 How to improve", expanded=False):
                        st.markdown(suggestions[section])

            # 🎯 Job Role Tips
            role_suggestions = {
                "frontend": "Consider adding React, HTML, or CSS projects to show UI experience.",
                "backend": "Include backend tech like Node.js, Express, or MongoDB.",
                "data": "Highlight data analysis tools like Pandas, SQL, or Excel.",
                "ai": "Mention any ML models or AI projects using TensorFlow or NLP."
            }

            role_detected = None
            for role in role_suggestions:
                if role in raw_text.lower():
                    role_detected = role
                    break

            if role_detected:
                st.markdown("### 🎯 Tips for Your Target Role")
                st.info(role_suggestions[role_detected])

            # 🚀 Career Paths
            st.markdown("### 🚀 Career Paths That Fit You")
            skills = parsed.get("skills", [])
            roles = []
            if any(s in skills for s in ["react.js", "html5", "css3", "javascript"]): roles.append("Frontend Developer")
            if any(s in skills for s in ["node.js", "express.js", "mongodb"]): roles.append("Backend Developer")
            if any(s in skills for s in ["python", "sql", "pandas", "numpy"]): roles.append("Data Analyst")
            if any(s in skills for s in ["tensorflow", "keras", "scikit-learn"]): roles.append("AI/ML Engineer")
            if not roles: roles.append("General Software Developer")
            st.success(f"Based on your skills, you might enjoy being a: **{', '.join(roles)}**.")

        with right_col:
            st.subheader("🧠 Your Skills Overview")
            category_map = {cat: [] for cat in SKILL_CATEGORIES}
            for skill in parsed.get("skills", []):
                for cat, kw_list in SKILL_CATEGORIES.items():
                    if skill.lower() in kw_list:
                        category_map[cat].append(skill)
            category_map = {k: v for k, v in category_map.items() if v}

            if category_map:
                df = pd.DataFrame({
                    "Category": list(category_map.keys()),
                    "Count": [len(v) for v in category_map.values()],
                    "Skills": [", ".join(v) for v in category_map.values()]
                })
                fig = px.pie(df,
                             names="Category",
                             values="Count",
                             hole=0.3,
                             custom_data=["Skills"],
                             title="Tech Skills Grouped by Type")
                fig.update_traces(hovertemplate="<b>%{label}</b><br>%{customdata[0]}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tech skills found to display.")

            # 💾 Download Button
            with open(pdf_path, "rb") as f:
                st.download_button("💾 Save Your Resume Report", f, file_name="parsed_resume.pdf", mime="application/pdf")
