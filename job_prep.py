import pandas as pd
import re
import os

JOBS_CSV_PATH = r"C:\Users\khushi tyagi\Major project -2 (JOB - TALK)\backend\job description\postings.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "cleaned_jobs.csv")

MASTER_SKILLS = {"python", "sql", "java", "machine learning", "data analysis", 
                 "excel", "communication", "sales", "marketing", "aws", "azure", 
                 "accounting", "tally", "cad", "agile", "react", "node", "fastapi", "numpy", "pandas"}

def clean_text(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_skills(clean_text_string):
    words = set(clean_text_string.split())
    found_skills = list(words.intersection(MASTER_SKILLS))
    for skill in MASTER_SKILLS:
        if " " in skill and skill in clean_text_string:
            if skill not in found_skills: found_skills.append(skill)
    return found_skills

def process_jobs():
    print(f"Looking for raw dataset at: {JOBS_CSV_PATH}")
    if not os.path.exists(JOBS_CSV_PATH):
        print("❌ ERROR: Cannot find postings.csv!")
        print("Check if your 'job description.zip' was extracted properly into that folder.")
        return

    try:
        print("Loading dataset... (This might take a minute for a big CSV)")
        df = pd.read_csv(JOBS_CSV_PATH, usecols=['job_id', 'title', 'description'])
        df = df.dropna(subset=['description'])
        
        print(f"Processing {len(df)} job postings...")
        df['clean_description'] = df['description'].apply(clean_text)
        df['required_skills'] = df['clean_description'].apply(lambda x: ", ".join(extract_skills(x)))
        
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"\n✅ SUCCESS! Cleaned jobs saved to: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    process_jobs()