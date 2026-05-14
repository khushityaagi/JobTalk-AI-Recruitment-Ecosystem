from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

bert_model = SentenceTransformer('paraphrase-MiniLM-L3-v2', device='cpu')

TECH_KEYWORDS = [
    'python', 'machine learning', 'sql', 'java', 'tensorflow',
    'pandas', 'aws', 'docker', "react", 'javascript', 'pytorch',
    'data analysis', 'deep learning', 'tableau', 'power bi'
]

def calculate_match_score(resume_text, job_description):
    resume_lower = resume_text.lower()
    job_lower = job_description.lower()

    # 1. SKILL MATCHING
    required_by_job = [skill for skill in TECH_KEYWORDS if skill in job_lower]
    matched_skills = [skill for skill in required_by_job if skill in resume_lower]

    # 2. SENTENCE-BERT SEMANTIC SIMILARITY
    embeddings = bert_model.encode([resume_lower, job_lower])
    base_similarity = float(cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0]) * 100

    # 3. SKILL BOOST
    if len(matched_skills) >= 3:
        boost = 35.0
    elif len(matched_skills) >= 1:
        boost = 15.0
    else:
        boost = 0.0

    skill_multiplier = len(matched_skills) * 2.25

    # 4. FINAL SCORE
    if base_similarity < 5 and len(matched_skills) == 0:
        return round(base_similarity, 2)

    final_score = base_similarity + boost + skill_multiplier
    return min(round(final_score, 2), 98.5)