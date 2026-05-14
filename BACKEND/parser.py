import pdfplumber
import docx
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    nltk.download('wordnet')

STOP_WORDS = set(stopwords.words('english'))
LEMMATIZER = WordNetLemmatizer()

SKILLS = [
    "python","java","c++","sql","machine learning","data analysis",
    "deep learning","tensorflow","pandas","numpy","excel","power bi",
    "tableau","aws","docker","html","css","javascript"
]

def clean_text(text):
    """Data Science cleaning: Removes noise, emails, symbols, and lemmatizes."""
    if not text: return ""
    
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text)  
    text = re.sub(r'http\S+|www\S+', '', text)  
    text = re.sub(r'[^a-z\s]', ' ', text)  
    
    words = text.split()
    cleaned = [LEMMATIZER.lemmatize(w) for w in words if w not in STOP_WORDS and len(w) > 2]
    
    return " ".join(cleaned)

def extract_text(file_path):
    raw_text = ""

    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                raw_text += page.extract_text() or ""

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        raw_text = "\n".join([para.text for para in doc.paragraphs])

    return clean_text(raw_text)

def parse_resume(text):
    """Uses the cleaned text to detect skills."""
    found_skills = []

    for skill in SKILLS:
    
        if re.search(rf"\b{re.escape(skill)}\b", text):
            found_skills.append(skill)

    return {
        "skills": list(set(found_skills)),
        "education": "Detected from resume text"
    }