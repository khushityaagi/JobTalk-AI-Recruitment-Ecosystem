from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_match_score(resume_text, job_description):
    """
    Matches candidate profiles with job requirements using TF-IDF and Cosine Similarity[cite: 89, 277].
    """
    
    documents = [resume_text, job_description]
    

    vectorizer = TfidfVectorizer(stop_words='english')
    
  
    tfidf_matrix = vectorizer.fit_transform(documents)
    

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
    return round(float(similarity[0][0]) * 100, 2)