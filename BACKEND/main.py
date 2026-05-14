from sentence_transformers import SentenceTransformer
from rapidfuzz import fuzz
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import mysql.connector
import pandas as pd
import re
import numpy as np 
from sklearn.metrics.pairwise import cosine_similarity

from parser import extract_text, parse_resume

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

bert_model = SentenceTransformer(
    'paraphrase-MiniLM-L3-v2',   
    device='cpu'
)
SKILL_DB = [
    "python", "java", "javascript", "typescript", "c++", "c#", "r", "scala", "go", "rust",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring boot",
    "rest api", "graphql", "html", "css",
    "machine learning", "deep learning", "natural language processing", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "hugging face", "bert", "llm",
    "reinforcement learning", "time series", "recommendation system",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "power bi", "tableau",
    "excel", "data analysis", "data visualization", "statistics",
    "sql", "mysql", "postgresql", "mongodb", "redis", "firebase", "elasticsearch",
    "oracle", "sqlite",
    "aws", "azure", "google cloud", "docker", "kubernetes", "ci/cd", "jenkins",
    "git", "github", "linux", "terraform", "airflow",
    "spark", "hadoop", "kafka", "hive", "databricks",
    "communication", "teamwork", "problem solving", "project management", "agile", "scrum"
]
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_live_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text)      
    text = re.sub(r'http\S+', '', text)      
    text = re.sub(r'[^a-zA-Z\s]', ' ', text) 
    return re.sub(r'\s+', ' ', text).strip()

jobs_df = pd.DataFrame()
resumes_df = pd.DataFrame()

@app.on_event("startup")
async def startup_event():
    global jobs_df, resumes_df
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        jobs_paths = ["cleaned_jobs.csv", "linkedin_jobs.csv", "jobs.csv"]
        for path in jobs_paths:
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                jobs_df = pd.read_csv(full_path)

                if "clean_description" not in jobs_df.columns:
                    jobs_df["clean_description"] = ""
                jobs_df["clean_description"] = jobs_df["clean_description"].fillna("").astype(str)

                print(f" AI Brain: Loaded {len(jobs_df)} jobs from {path}")
                break
    except Exception as e:
        print(f" Job Loading Error: {e}")
 
    try:
        resumes_paths = ["cleaned_resumes.csv", "resumes_dataset.csv", "resumes.csv"]
        for path in resumes_paths:
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                resumes_df = pd.read_csv(full_path)

                if 'clean_resume' not in resumes_df.columns:
                    col = 'Resume_Text' if 'Resume_Text' in resumes_df.columns else resumes_df.columns[0]
                    resumes_df['clean_resume'] = resumes_df[col]

                resumes_df['clean_resume'] = resumes_df['clean_resume'].fillna("").astype(str)

                print(f" AI Brain: Loaded {len(resumes_df)} resumes from {path}")
                break
    except Exception as e:
        print(f" Resume Loading Error: {e}")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ADD_YOUR_PASSWORD_HERE",
        database="job_talk",
        auth_plugin='mysql_native_password' 
    )

def calculate_similarity_bert(resume_text, job_list):
    if not job_list:
        return []

    try:
        embeddings = bert_model.encode([resume_text] + job_list)

        resume_vec = embeddings[0].reshape(1, -1)
        job_vecs = embeddings[1:]

        scores = cosine_similarity(resume_vec, job_vecs)[0]
        return scores

    except Exception as e:
        print(f"BERT Engine Error: {e}")
        return []
    
def extract_skills_hybrid(text):
    text_lower = text.lower()

    fuzzy_skills = [
        skill for skill in SKILL_DB
        if fuzz.partial_ratio(skill, text_lower) > 85
    ]

    text_emb = bert_model.encode([text])[0]
    skill_embs = bert_model.encode(SKILL_DB)

    bert_skills = []
    for i, skill_emb in enumerate(skill_embs):
        score = cosine_similarity([text_emb], [skill_emb])[0][0]
        if score > 0.4:
            bert_skills.append(SKILL_DB[i])

    return list(set(fuzzy_skills + bert_skills))

@app.post("/discover_jobs/")
async def discover_jobs(file: UploadFile = File(...)):
    if jobs_df.empty:
        return {"error": "AI dataset is offline. Please check backend console."}

    temp_path = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True) 
        
        temp_path = os.path.join(data_dir, f"temp_{file.filename}")
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        raw_resume_text = extract_text(temp_path)
        cleaned_resume_text = clean_live_text(raw_resume_text)

        
        filtered_df = jobs_df[jobs_df['clean_description'].str.len() > 100].copy()
        sample_size = min(1200, len(filtered_df)) 
        demo_sample = filtered_df.sample(sample_size)

        job_descriptions = demo_sample['clean_description'].tolist()
        job_titles = demo_sample['title'].tolist()
        job_ids = demo_sample['job_id'].tolist()

        scores = calculate_similarity_bert(cleaned_resume_text, job_descriptions)
        scores = np.array(scores, dtype=float)

        if len(scores) == 0:
            return {"recommendations": []}

        if len(scores) > 0 and max(scores) > 0:
            scores = scores / float(max(scores))
  
        recommendations = []

        for i, score in enumerate(scores):
            if score < 0.5:   
                continue

            final_score = round(float(score) * 100)

            recommendations.append({
                "id": str(job_ids[i]),
                "title": str(job_titles[i]),
                "score": float(final_score)
            })
            
        for rec in recommendations:
            if rec["score"] > 75:
                rec["label"] = "Strong Match"
            elif rec["score"] > 60:
                rec["label"] = "Moderate Match"
            else:
                rec["label"] = "Low Match"

        top_matches = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:5]

        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

        return {"recommendations": top_matches}

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return {"error": str(e)}

@app.post("/upload_resume/")
async def upload_resume(user_id: int = Form(...), job_id: int = Form(...), file: UploadFile = File(...)):
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        upload_dir = os.path.join(base_dir, "data")
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text(file_path)
        data = parse_resume(text)

        resume_skills = set(extract_skills_hybrid(clean_live_text(text)))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
  
        cursor.execute("SELECT description FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        job_desc = str(job['description']) if job and job['description'] else ""

        clean_resume = clean_live_text(text)
        clean_job = clean_live_text(job_desc)

        embeddings = bert_model.encode([clean_resume, clean_job])
        semantic_score = cosine_similarity(
            embeddings[0].reshape(1, -1),
            embeddings[1].reshape(1, -1)
        )[0][0]

        resume_skills = set(extract_skills_hybrid(clean_resume))
        job_skills = set(extract_skills_hybrid(clean_job))

        common_skills = resume_skills & job_skills

        if len(job_skills) > 0:
            skill_score = len(common_skills) / len(job_skills)
        else:
            skill_score = 0

        final_score = (0.6 * semantic_score) + (0.4 * skill_score)

        score = float(round(final_score * 100, 2))

        missing_skills = list(job_skills - resume_skills)

        skills_str = ", ".join(resume_skills)
        sql = "INSERT INTO resumes (user_id, raw_text, skills_detected) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, text, skills_str))
        conn.commit()

        return {
            "match_score": score,
            "skills_detected": list(resume_skills),
            "missing_skills": missing_skills
        }
    except Exception as e:
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
        if not job: return {"error": "Job not found"}

        cursor.execute("SELECT id, user_id, raw_text, skills_detected FROM resumes")
        resumes = cursor.fetchall()
        if not resumes: return {"error": "No resumes in database"}

        resume_texts = [r["raw_text"] for r in resumes]

        embeddings = bert_model.encode([job["description"]] + resume_texts)

        job_vec = embeddings[0].reshape(1, -1)
        resume_vecs = embeddings[1:]

        scores = cosine_similarity(job_vec, resume_vecs)[0]

        if len(scores) > 0 and max(scores) > 0:
            scores = scores / max(scores)

        ranked_candidates = []

        for i, score in enumerate(scores):
            ranked_candidates.append({
                "resume_id": resumes[i]["id"],
                "user_id": resumes[i]["user_id"],
                "match_score": float(round(score * 100, 2)),
                "detected_skills": resumes[i]["skills_detected"]
            })

        top_candidates = sorted(
            ranked_candidates,
            key=lambda x: x["match_score"],
            reverse=True
        )[:10]

        return {
            "job_title": job["title"],
            "top_candidates": top_candidates
        }

    finally:
        if conn:
            conn.close()  

@app.get("/get_jobs/")
async def get_jobs():
    """Returns a fixed list of 10 professional roles for a stable dashboard experience"""
    try:
    
        standard_roles = [
            {"id": "1", "title": "Data Scientist", "company": "AI Solutions", "location": "Remote"},
            {"id": "2", "title": "Python Developer", "company": "TechCorp", "location": "San Francisco, CA"},
            {"id": "3", "title": "Software Engineer", "company": "Global Systems", "location": "New York, NY"},
            {"id": "4", "title": "DevOps Engineer", "company": "CloudStream", "location": "Remote"},
            {"id": "5", "title": "Machine Learning Engineer", "company": "NeuralNet", "location": "Austin, TX"},
            {"id": "6", "title": "Project Manager", "company": "Business Partners", "location": "Chicago, IL"},
            {"id": "7", "title": "Business Analyst", "company": "Insight Data", "location": "Boston, MA"},
            {"id": "8", "title": "HR Specialist", "company": "People First", "location": "Remote"},
            {"id": "9", "title": "Marketing Manager", "company": "Growth Hub", "location": "Seattle, WA"},
            {"id": "10", "title": "Financial Accountant", "company": "Finance Pros", "location": "Denver, CO"}
        ]
        
        return {"jobs": standard_roles}
    except Exception as e:
        print(f"Discovery Feed Error: {e}")
        return {"jobs": [], "error": str(e)}

@app.post("/recruiter_scan/") 
async def recruiter_scan(job_description: str = Form(...)):
    if resumes_df.empty:
        return {"error": "Candidate database is offline."}

    try:
        cleaned_job = clean_live_text(job_description)
        job_lower = job_description.lower()

    
        target_category = "ENGINEERING"
        if any(k in job_lower for k in ['python', 'ai', 'data', 'ml']):
            target_category = "ENGINEERING"
        elif any(k in job_lower for k in ['account', 'finance', 'tax']):
            target_category = "ACCOUNTANT"

        if "Category" in resumes_df.columns:
            filtered_df = resumes_df[resumes_df['Category'] == target_category].copy()
        else:
            filtered_df = resumes_df.copy()
        if filtered_df.empty:
            filtered_df = resumes_df.sample(min(200, len(resumes_df)))

        candidate_texts = filtered_df['clean_resume'].tolist()[:200]

        embeddings = bert_model.encode([cleaned_job] + candidate_texts,batch_size=32)

        job_vec = embeddings[0].reshape(1, -1)
        candidate_vecs = embeddings[1:]

        scores = cosine_similarity(job_vec, candidate_vecs)[0]

        if len(scores) > 0 and max(scores) > 0:
            scores = scores / max(scores)

        candidates_results = []

        for i, score in enumerate(scores):
            if score < 0.5:   
                continue

            res_text = str(candidate_texts[i]).lower()
    
            resume_words = set(res_text.split())
            job_words = set(job_lower.split())
            common_skills = list(resume_words.intersection(job_words))[:3]
    
            candidates_results.append({
                "name": f"Candidate_{filtered_df.iloc[i].get('ID', i)}.pdf",
                "category": str(filtered_df.iloc[i].get('Category', target_category)),
                "score": float(round(score * 100, 2)),   
                "matched_skills": common_skills
            })

        top_candidates = sorted(candidates_results, key=lambda x: x['score'], reverse=True)[:10]

        return {
            "candidates": top_candidates
        }

    except Exception as e:
        print(f"Recruiter Scan Error: {e}")
        return {"error": "Failed to analyze candidate pool."}
    