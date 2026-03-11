from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import mysql.connector
import pandas as pd
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from parser import extract_text, parse_resume
from matching import calculate_match_score
from chatbot import get_chatbot_response

app = FastAPI()

def clean_live_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text)      # remove emails
    text = re.sub(r'http\S+', '', text)      # remove URLs
    text = re.sub(r'[^a-zA-Z\s]', ' ', text) # remove symbols
    return re.sub(r'\s+', ' ', text).strip()

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Loading AI Datasets into memory for lightning-fast matching...")

try:
    jobs_csv_path = os.path.join(base_dir, "cleaned_jobs.csv")
    jobs_df = pd.read_csv(jobs_csv_path) 
    jobs_df['clean_description'] = jobs_df['clean_description'].fillna("") 
    print(f"✅ Loaded {len(jobs_df)} LinkedIn jobs.")
except Exception as e:
    print(f"⚠️ Warning: Could not load LinkedIn jobs. ({e})")
    jobs_df = pd.DataFrame()

try:
    resumes_csv_path = os.path.join(base_dir, "all_resumes.csv")
    resumes_df = pd.read_csv(resumes_csv_path)
    resumes_df['Cleaned_Text'] = resumes_df['Cleaned_Text'].fillna("")
    print(f"✅ Loaded {len(resumes_df)} Student Resumes.")
except Exception as e:
    print(f"⚠️ Warning: Could not load Student Resumes. ({e})")
    resumes_df = pd.DataFrame()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sj8=63GpJ",
        database="job_talk"
    )

def calculate_bulk_similarity(resume_text, job_list):
    if not job_list:
        return []
    vectorizer = TfidfVectorizer(stop_words='english')
    all_texts = [resume_text] + job_list
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    # Compare resume (index 0) with all jobs (index 1 onwards)
    scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    return scores[0]

@app.get("/get_jobs/")
async def get_jobs():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title FROM jobs LIMIT 50")
        jobs = cursor.fetchall()
        return jobs
    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn: conn.close()

@app.post("/discover_jobs/")
async def discover_jobs(file: UploadFile = File(...)):
    if jobs_df.empty:
        return {"error": "AI dataset is offline. Please check backend console."}

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        temp_path = os.path.join(base_dir, "data", f"temp_{file.filename}")
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
          
        raw_resume_text = extract_text(temp_path)
        cleaned_resume_text = clean_live_text(raw_resume_text)

        job_descriptions = jobs_df['clean_description'].tolist()
        job_titles = jobs_df['title'].tolist()
        job_ids = jobs_df['job_id'].tolist()

        scores = calculate_bulk_similarity(cleaned_resume_text, job_descriptions)

        recommendations = []
        for i, score in enumerate(scores):
            if score > 0.02: # Lowered threshold slightly for broader matching
                recommendations.append({
                    "id": str(job_ids[i]),
                    "title": str(job_titles[i]),
                    "score": f"{round(score * 100, 2)}%"
                })

        top_matches = sorted(recommendations, key=lambda x: float(x['score'].replace('%','')), reverse=True)[:5]
        
        return {"recommendations": top_matches}

    except Exception as e:
        print(f"Discovery Error: {e}")
        return {"error": str(e)}

@app.post("/upload_resume/")
async def upload_resume(
    user_id: int = Form(...),
    job_id: int = Form(...),
    file: UploadFile = File(...)
):
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, "data")
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text(file_path)
        data = parse_resume(text)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        
        job_desc = job[0] if job else ""
        
        score = calculate_match_score(text, job_desc)
        
        
        resume_skills = [s.lower() for s in data.get("skills", [])]
        
        job_data = parse_resume(job_desc) 
        required_skills = [s.lower() for s in job_data.get("skills", [])] if job_data else []
        
        missing_skills = list(set(required_skills) - set(resume_skills))
        

        skills_str = ", ".join(data.get("skills", []))

        sql = "INSERT INTO resumes (user_id, raw_text, skills) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, text, skills_str))
        conn.commit()

        return {
            "match_score": f"{score}%",
            "skills_detected": data.get("skills", []),
            "missing_skills": missing_skills  # <-- NEW: Sending this back to the frontend
        }
    except Exception as e:
        print(f"\n--- ERROR DETECTED ---\n{e}\n----------------------")
        return {"error": str(e)}
    finally:
        if conn: conn.close()

@app.post("/recruiter_rank/")
async def recruiter_rank(job_id: int = Form(...)):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT title, description FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        if not job:
            return {"error": "Job not found"}

        cursor.execute("SELECT id, user_id, raw_text FROM resumes")
        resumes = cursor.fetchall()
        
        if not resumes:
            return {"error": "No resumes currently in the database"}

        resume_texts = [r['raw_text'] for r in resumes]

        vectorizer = TfidfVectorizer(stop_words='english')
        all_texts = [job['description']] + resume_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
       
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        ranked_candidates = []
        for i, score in enumerate(scores):
            ranked_candidates.append({
                "resume_id": resumes[i]['id'],
                "user_id": resumes[i]['user_id'],
                "match_score": f"{round(score * 100, 2)}%"
            })

        top_candidates = sorted(ranked_candidates, key=lambda x: float(x['match_score'].replace('%','')), reverse=True)[:10]

        return {"job_title": job['title'], "top_candidates": top_candidates}

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn: conn.close()

@app.get("/chat/")
async def chat_with_bot(query: str, user_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT raw_text, skills FROM resumes WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        
        resume_text = result['raw_text'] if result and result['raw_text'] else "No resume uploaded yet."
        skills = result['skills'] if result and result['skills'] else "None"

        response = get_chatbot_response(query, resume_text, skills)
        return {"bot_response": response}
    except Exception as e:
        print(f"BACKEND ERROR: {e}") 
        return {"error": str(e)}
    finally:
        if conn: conn.close()

@app.post("/recruiter_match/")
async def recruiter_match(job_description: str = Form(...)):
    if resumes_df.empty:
        return {"error": "Candidate database is offline."}

    try:
        
        cleaned_job = clean_live_text(job_description)

        
        candidate_texts = resumes_df['Cleaned_Text'].tolist()
        candidate_ids = resumes_df['Candidate_ID'].tolist()
        candidate_categories = resumes_df['Category'].tolist()

       
        all_texts = [cleaned_job] + candidate_texts
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

    
        recommendations = []
        for i, score in enumerate(scores):
            if score > 0.05: # Only show decent matches
                recommendations.append({
                    "candidate_id": str(candidate_ids[i]),
                    "category": str(candidate_categories[i]),
                    "match_score": f"{round(score * 100, 2)}%"
                })

        top_candidates = sorted(recommendations, key=lambda x: float(x['match_score'].replace('%','')), reverse=True)[:10]
        
        return {"top_candidates": top_candidates}

    except Exception as e:
        print(f"Recruiter Matching Error: {e}")
        return {"error": str(e)}