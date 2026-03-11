import pandas as pd
import re
import os
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_CSV = os.path.join(BASE_DIR, "job description", "postings.csv")
RESUME_PDF = os.path.join(BASE_DIR, "data", "khushi_resume.pdf") 
def clean_text(text):
    """Removes junk, punctuation, and makes everything lowercase."""
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text) # 
    text = re.sub(r'http\S+', '', text) # 
    text = re.sub(r'[^a-z\s]', ' ', text) 
    return re.sub(r'\s+', ' ', text).strip() 

print("\n" + "="*50)
print(" PHASE 1: LOADING & CLEANING A JOB POSTING")
print("="*50)

try:
  
    df = pd.read_csv(JOBS_CSV, nrows=5, usecols=['job_id', 'title', 'description'])
    
    raw_job = df.iloc[0]['description']
    job_title = df.iloc[0]['title']
    cleaned_job = clean_text(raw_job)
    
    print(f"TARGET ROLE: {job_title}")
    print(f"\nRAW TEXT (First 200 chars):\n{raw_job[:200]}...")
    print(f"\nCLEANED TEXT (First 200 chars):\n{cleaned_job[:200]}...")
    
except Exception as e:
    print(f"Could not load jobs: {e}")
    cleaned_job = ""

print("\n" + "="*50)
print(" PHASE 2: LOADING & CLEANING YOUR RESUME")
print("="*50)

try:
    with open(RESUME_PDF, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        raw_resume = " ".join([page.extract_text() for page in reader.pages])
        
    cleaned_resume = clean_text(raw_resume)
    print(f"RAW RESUME (First 200 chars):\n{raw_resume[:200]}...")
    print(f"\nCLEANED RESUME (First 200 chars):\n{cleaned_resume[:200]}...")
    
except Exception as e:
    print(f"Could not load resume: {e}")
    cleaned_resume = ""

print("\n" + "="*50)
print(" PHASE 3: THE AI MATH (TF-IDF & COSINE SIMILARITY)")
print("="*50)

if cleaned_job and cleaned_resume:
    
    vectorizer = TfidfVectorizer(stop_words='english')
    
    
    corpus = [cleaned_job, cleaned_resume]
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
    score = round(similarity[0][0] * 100, 2)
    print(f"MATHEMATICAL MATCH SCORE: {score}%")
    
   
    feature_names = vectorizer.get_feature_names_out()
    print(f"\nTotal unique vocabulary words analyzed: {len(feature_names)}")
else:
    print("Missing data to perform calculation.")
print("\n" + "="*50 + "\n")