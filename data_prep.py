import os
import re
import pandas as pd
import PyPDF2

BASE_DIR = r"C:\Users\khushi tyagi\Major project -2 (JOB - TALK)\backend\resume\data\data"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "cleaned_resumes.csv")

MASTER_SKILLS = {
    "python", "sql", "java", "machine learning", "data analysis", 
    "excel", "communication", "sales", "marketing", "aws", "azure", 
    "accounting", "tally", "cad", "agile"
}

def clean_text(text):
    """Cleans text using pure regex instead of NLP libraries."""
    if not isinstance(text, str): return "" 
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text) # 
    text = re.sub(r'http\S+', '', text) # 
    text = re.sub(r'[^a-z\s]', ' ', text) 
    return re.sub(r'\s+', ' ', text).strip() 

def extract_skills(clean_text_string):
    """Finds skills by intersecting resume words with our Master List."""
    words = set(clean_text_string.split())
    found_skills = list(words.intersection(MASTER_SKILLS))
    
   
    for skill in MASTER_SKILLS:
        if " " in skill and skill in clean_text_string:
            if skill not in found_skills:
                found_skills.append(skill)
                
    return found_skills

def process_resumes():
    print(f"Scanning directory: {BASE_DIR}")
    if not os.path.exists(BASE_DIR):
        print("❌ ERROR: Cannot find the resume folders! Check the path again.")
        return

    dataset = []
    
    
    for category in os.listdir(BASE_DIR):
        category_path = os.path.join(BASE_DIR, category)
        
        if os.path.isdir(category_path):
            print(f"Processing category: {category}...")
            
            for filename in os.listdir(category_path):
                if filename.endswith(".pdf"):
                    filepath = os.path.join(category_path, filename)
                    
                    try:
                        # Extract text from PDF
                        with open(filepath, "rb") as file:
                            reader = PyPDF2.PdfReader(file)
                            text = ""
                            for page in reader.pages:
                                extracted = page.extract_text()
                               
                                if extracted: 
                                    text += extracted + " "
                                    
                        
                        cleaned = clean_text(text)
                        skills = extract_skills(cleaned)
                        
                        dataset.append({
                            "Category": category,
                            "Filename": filename,
                            "Clean_Text": cleaned,
                            "Extracted_Skills": ", ".join(skills)
                        })
                    except Exception as e:
                        
                        pass 


    if dataset:
        df = pd.DataFrame(dataset)
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"\n✅ Extraction complete! Saved {len(df)} resumes to: {OUTPUT_PATH}")
    else:
        print("\n❌ No resumes were processed.")

if __name__ == "__main__":
    process_resumes()