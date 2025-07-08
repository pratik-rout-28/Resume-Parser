# app/exporter.py

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import json
import re

def export_resume(json_path: str, pdf_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Setup PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=LETTER,
                            leftMargin=1*inch, rightMargin=1*inch,
                            topMargin=1*inch, bottomMargin=1*inch)

    styles = getSampleStyleSheet()
    content = []

    # Custom styles
    heading = styles["Heading2"]
    normal = styles["Normal"]
    bold = ParagraphStyle(name="Bold", parent=normal, fontName="Helvetica-Bold")

    # Header
    content.append(Paragraph(f"<b>{data.get('name', '')}</b>", styles["Title"]))
    content.append(Paragraph(f"Phone: {data.get('phone', '')}", normal))
    content.append(Paragraph(f"Email: {data.get('email', '')}", normal))
    if data.get("linkedin"):
        content.append(Paragraph(f"LinkedIn: {data['linkedin']}", normal))
    if data.get("github"):
        content.append(Paragraph(f"GitHub: {data['github']}", normal))
    content.append(Spacer(1, 12))

    # Summary
    if data.get("summary"):
        content.append(Paragraph("Summary", heading))
        content.append(Paragraph(data["summary"], normal))
        content.append(Spacer(1, 12))

    # Skills
    if data.get("skills"):
        content.append(Paragraph("Skills", heading))
        for skill in data["skills"]:
            content.append(Paragraph(f"• {skill}", normal))
        content.append(Spacer(1, 12))

    # Projects
    if data.get("projects"):
        content.append(Paragraph("Projects", heading))
        for proj in data["projects"]:
            content.append(Paragraph(f"<b>{proj['title']}</b>", bold))
            content.append(Paragraph(proj["description"], normal))
            if proj.get("technologies"):
                content.append(Paragraph(f"<i>Technologies:</i> {', '.join(proj['technologies'])}", normal))
            content.append(Spacer(1, 10))

    # Education
    if data.get("education"):
        content.append(Paragraph("Education", heading))
        edu_list = data["education"]

        # Group in pairs: [institute + duration, degree]
        for i in range(0, len(edu_list) - 1, 2):
            line = f"{edu_list[i]} ({edu_list[i + 1]})"
            content.append(Paragraph(f"• {line}", normal))

        content.append(Spacer(1, 12))
        
    # Build PDF
    doc.build(content)
    print(f"✅ PDF written to {pdf_path}")
