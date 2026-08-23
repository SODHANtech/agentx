import json
import fitz

from backend.llm import llm


class ResumeAgent:

    def extract_text(self, pdf_path: str):

        document = fitz.open(pdf_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text

    def analyze_resume(self, pdf_path: str):

        resume = self.extract_text(pdf_path)

        prompt = f"""
You are an expert ATS Resume Analyzer.

Analyze the following resume.

Return ONLY VALID JSON.

Format:

{{
    "ats_score": 0,
    "skills": [],
    "strengths": [],
    "weaknesses": [],
    "missing_skills": [],
    "recommended_projects": [],
    "recommended_certifications": [],
    "recommended_companies": [],
    "summary": ""
}}

Rules:

- ATS score must be between 0 and 100.
- Mention all technical skills.
- Suggest missing technical skills.
- Recommend 3 projects.
- Recommend certifications.
- Recommend companies suitable for the candidate.
- Return ONLY JSON.

Resume:

{resume}
"""

        response = llm.invoke(prompt)

        text = response.content.strip()

        text = (
            text.replace("```json", "")
                .replace("```", "")
                .strip()
        )

        try:
            return json.loads(text)

        except Exception:

            return {
                "error": "LLM returned invalid JSON.",
                "raw_output": text
            }