import os
import json
import base64
import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from app.extractor import extract_text_from_pdf
from app.parser import parse_resume, score_resume
from app.exporter import export_resume
from app.utils import SKILL_CATEGORIES

# ---------- Page Config ----------
st.set_page_config(page_title="AI-Powered Resume Parser", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    .stApp {
        background-color:#0e0e11; color:#FEFEFA;
    }
    .block-container {
        padding:2rem;
    }
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
        margin-right:12px;
    }
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        .subtext {
            font-size: 0.95rem;
        }
        .block-container {
            padding: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Title ----------
st.markdown('<div class="main-title">🤖 AI-Powered Resume Parser</div>', unsafe_allow_html=True)
st.markdown('<div class="subtext">A simple and smart tool that reads resumes and instantly picks out important details like skills and experience.</div>', unsafe_allow_html=True)

# ---------- File Upload ----------
uploaded_file = st.file_uploader("📤 Upload your resume (PDF only)", type=["pdf"])

if uploaded_file:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > 2:
        st.error("❌ File too large. Please upload a PDF smaller than 2 MB.")
    else:
        steps = ["📤 Upload", "🧠 Extract", "🔍 Parse", "📄 Export", "✅ Done"]
        badge_placeholder = st.empty()

        def render_badges(active_idx: int):
            html = "<div style='font-size:1rem; margin-bottom:1rem; display:flex; gap:1rem; flex-wrap:wrap;'>"
            for i, label in enumerate(steps):
                bg = "#1976D2" if i <= active_idx else "#424242"
                html += f"<span style='background:{bg}; color:white; padding:6px 12px; border-radius:20px;'>{label}</span>"
            html += "</div>"
            badge_placeholder.markdown(html, unsafe_allow_html=True)

        render_badges(0)

        progress = st.progress(0, text="📄 Processing resume...")

        # Step 1 – Save file
        os.makedirs("resumes", exist_ok=True)
        resume_path = os.path.join("resumes", uploaded_file.name)
        with open(resume_path, "wb") as f:
            f.write(uploaded_file.read())
        progress.progress(25, text="📥 File saved successfully.")
        render_badges(1)

        # Step 2 – Extract text
        raw_text = extract_text_from_pdf(resume_path)
        progress.progress(50, text="🧠 Extracting text from PDF...")
        render_badges(2)

        # Step 3 – Parse resume
        parsed = parse_resume(raw_text)
        score_breakdown = score_resume(parsed)
        progress.progress(75, text="🔍 Parsing resume content...")
        render_badges(3)

        # Step 4 – Export files
        os.makedirs("output", exist_ok=True)
        json_path = "output/parsed_resume.json"
        pdf_path = "output/parsed_resume.pdf"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=4)
        export_resume(json_path, pdf_path)
        progress.progress(100, text="✅ Completed!")
        render_badges(4)

        st.success("✅ Resume parsed and converted successfully!")

        # ---------- Resume Summary + PDF ----------
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.subheader("📋 ATS Report")
            st.markdown(f"### ✅ Your Score: **{score_breakdown['Total Score']} / 100**")

            suggestions = {
                "Contact Info": "Add both email and phone number to complete your contact details.",
                "Social Links": "Include both LinkedIn and GitHub profiles to increase your credibility.",
                "Skills": "List at least 5 relevant technical skills to showcase your capabilities.",
                "Projects": "Mention at least 2 projects with tech stacks and outcomes.",
                "Education": "Make sure your education history includes both school and college.",
                "Work Experience": "Add any work, internship, or volunteer experience for higher impact.",
                "Summary": "Include a short summary that highlights your goals and strengths."
            }

            max_points = {
                "Contact Info": 20,
                "Social Links": 10,
                "Skills": 15,
                "Projects": 15,
                "Education": 10,
                "Work Experience": 15,
                "Summary": 15
            }

            for section, pts in score_breakdown.items():
                if section == "Total Score":
                    continue
                emoji = "✅" if pts == max_points[section] else "⚠️" if pts > 0 else "❌"
                st.markdown(f"**{emoji} {section}**")
                if pts < max_points[section]:
                    with st.expander("💡 Suggestion", expanded=False):
                        st.markdown(suggestions[section])

            # ---------- Pie Chart for Skill Categories ----------
            st.markdown("### 📊 Skill Category Distribution")

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
                             title="Skill Distribution by Category")
                fig.update_traces(hovertemplate="<b>%{label}</b><br>%{customdata[0]}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No skills found to display.")

        with right_col:
            st.subheader("📄 Resume Preview")
            with open(pdf_path, "rb") as pdf_file:
                base64_pdf = base64.b64encode(pdf_file.read()).decode("utf-8")
                pdf_html = f"""
                <iframe src="data:application/pdf;base64,{base64_pdf}" 
                        width="100%" height="600px" type="application/pdf">
                </iframe>
                """
                components.html(pdf_html, height=600)

            with open(pdf_path, "rb") as f:
                st.download_button("⬇️ Download PDF", f, file_name="parsed_resume.pdf")
