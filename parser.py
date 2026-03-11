import pdfplumber
import docx
import re


SKILLS = [
    "python","java","c++","sql","machine learning","data analysis",
    "deep learning","tensorflow","pandas","numpy","excel","power bi",
    "tableau","aws","docker","html","css","javascript"
]

def extract_text(file_path):
    text = ""

    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])

    return text.lower()


def parse_resume(text):

    found_skills = []

    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill)

    return {
        "skills": list(set(found_skills)),
        "education": "Detected from resume text"
    }