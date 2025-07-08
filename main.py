import os
import json
from app.extractor import extract_text_from_pdf
from app.parser import parse_resume
from app.exporter import export_resume  # ✅ NEW import

def main():
    resume_path = "resumes/Resume.pdf"
    json_path = "output/parsed_resume.json"
    pdf_path = "output/parsed_resume.pdf"

    # Step 1: Extract text
    raw_text = extract_text_from_pdf(resume_path)

    # Step 2: Parse data
    parsed_data = parse_resume(raw_text)

    # Step 3: Save to JSON
    os.makedirs("output", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=4)
    print("✅ Resume parsed successfully! Check output/parsed_resume.json")

    # ✅ Step 4: Export to PDF
    export_resume(json_path, pdf_path)
    print("✅ Resume exported to PDF! Check output/parsed_resume.pdf")

if __name__ == "__main__":
    main()
