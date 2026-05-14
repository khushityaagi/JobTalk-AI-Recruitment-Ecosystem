import re
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

nltk.download('stopwords')
nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def deep_clean_text(text):
    if not isinstance(text, str): return ""
    
    text = re.sub(r'\S+@\S+', '', text) 
    text = re.sub(r'http\S+|www\S+', '', text) 
    text = re.sub(r'[^a-zA-Z\s]', ' ', text) 
    
    words = text.lower().split()
    
    cleaned = [lemmatizer.lemmatize(w) for w in words if w not in stop_words and len(w) > 2]
    
    return " ".join(cleaned)

def process_linkedin_data():
    print("Loading 123k LinkedIn records...")
    df = pd.read_csv("postings.csv") 
    
    df = df[['job_id', 'title', 'description']]
    
    print("Cleaning Job Descriptions (this may take a few minutes)...")
    df['clean_description'] = df['description'].apply(deep_clean_text)
    
    df.to_csv("cleaned_jobs.csv", index=False)
    print("Saved cleaned_jobs.csv")
