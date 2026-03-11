import os
import re
import pandas as pd
import PyPDF2


RESUME_DIR = r"C:\Users\khushi tyagi\Major project -2 (JOB - TALK)\backend\resume\data\data"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, "all_resumes.csv")

def clean_text(text):
    """Removes junk, punctuation, and makes everything lowercase."""
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'\S+@\S+', '', text) # Remove emails
    text = re.sub(r'http\S+', '', text) # Remove URLs
    text = re.sub(r'[^a-z\s]', ' ', text) # Keep ONLY letters and spaces
    return re.sub(r'\s+', ' ', text).strip() 

def build_resume_dataset():
    print(f"Scanning directory: {RESUME_DIR}")
    if not os.path.exists(RESUME_DIR):
        print("❌ ERROR: Cannot find the resume folders! Check the path again.")
        return

    dataset = []
    categories = os.listdir(RESUME_DIR)
    
    print(f"Found {len(categories)} job categories. Starting extraction...")
    print("This may take a few minutes as it reads hundreds of PDFs. Please wait...\n")
    
    for category in categories:
        category_path = os.path.join(RESUME_DIR, category)
        
        if os.path.isdir(category_path):
            files = os.listdir(category_path)
            print(f"Extracting {category} ({len(files)} resumes)...")
            
            for filename in files:
                if filename.endswith(".pdf"):
                    filepath = os.path.join(category_path, filename)
                    try:
                        with open(filepath, "rb") as file:
                            reader = PyPDF2.PdfReader(file)
                            raw_text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
                            
                            cleaned_text = clean_text(raw_text)
                            
                            dataset.append({
                                "Candidate_ID": f"{category}_{filename.replace('.pdf', '')}",
                                "Category": category,
                                "Cleaned_Text": cleaned_text
                            })
                    except Exception as e:
                        pass 


    if dataset:
        df = pd.DataFrame(dataset)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n✅ SUCCESS! {len(df)} resumes extracted, cleaned, and saved to: {OUTPUT_CSV}")
    else:
        print("\n❌ No resumes were processed. Check your folder structure.")

if __name__ == "__main__":
    build_resume_dataset()