import os
import pandas as pd

from parser import extract_text 
from cleaner_tool import deep_clean_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
resume_base_path = os.path.join(BASE_DIR, "resume", "data", "data")
postings_path = os.path.join(BASE_DIR, "job description", "postings.csv")
skills_path = os.path.join(BASE_DIR, "job description", "jobs", "job_skills.csv")

all_data = []
if not os.path.exists(resume_base_path):
    print(f" ERROR: Cannot find resume folder at {resume_base_path}")
else:
    print(f" Starting: Flattening and cleaning 2,400+ resumes from {resume_base_path}...")
    for category in os.listdir(resume_base_path):
        cat_path = os.path.join(resume_base_path, category)
        if os.path.isdir(cat_path):
            for file in os.listdir(cat_path):
                file_path = os.path.join(cat_path, file)
                try:
                   
                    cleaned_text = extract_text(file_path) 
                    all_data.append({"ID": file, "Category": category, "clean_resume": cleaned_text})
                except Exception as e:
                    print(f" Skipping file {file}: {e}")

    df_res = pd.DataFrame(all_data)
    
    df_res['clean_resume'] = df_res['clean_resume'].fillna("").astype(str)
    df_res.to_csv(os.path.join(BASE_DIR, "cleaned_resumes.csv"), index=False)
    print(" Created cleaned_resumes.csv")

print(" Starting: Merging LinkedIn Skills with Postings...")
try:

    if not os.path.exists(postings_path) or not os.path.exists(skills_path):
        raise FileNotFoundError("Missing postings.csv or job_skills.csv in 'job description' folder.")

    postings = pd.read_csv(postings_path)
    skills = pd.read_csv(skills_path)

    skills_grouped = skills.groupby('job_id')['skill_abr'].apply(lambda x: ' '.join(x.astype(str))).reset_index()

    merged_jobs = pd.merge(postings, skills_grouped, on='job_id', how='left')

    def super_clean(row):
    
        skill_text = str(row['skill_abr']) if pd.notna(row['skill_abr']) else ""
        desc_text = str(row['description']) if pd.notna(row['description']) else ""
        combined = f"{skill_text} {desc_text}"
      
        return deep_clean_text(combined)

    print(" Deep cleaning 123k jobs (This will take 5-10 minutes, please wait)...")
    merged_jobs['clean_description'] = merged_jobs.apply(super_clean, axis=1)

    merged_jobs = merged_jobs[merged_jobs['clean_description'].str.len() > 50]

    output_jobs_path = os.path.join(BASE_DIR, "cleaned_jobs.csv")

    merged_jobs[['job_id', 'title', 'clean_description']].to_csv(output_jobs_path, index=False)
    print(f" SUCCESS: Created cleaned_jobs.csv at {output_jobs_path}")

except Exception as e:
    print(f"FAILED to process jobs: {e}")