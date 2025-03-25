import torch
import spacy
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer

# Load spaCy model for NLP processing
nlp = spacy.load("en_core_web_sm")

# Load SBERT model for semantic similarity
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

# Function to extract skills using spaCy
def extract_skills(text):
    doc = nlp(text)
    skills = set()
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:  # Extract potential skills
            skills.add(token.text.lower())
    return skills

# Function to calculate SBERT-based similarity
def calculate_semantic_similarity(resume_skills, job_skills):
    if not resume_skills or not job_skills:
        return 0  # No skills available to compare
    
    resume_emb = sbert_model.encode(list(resume_skills), convert_to_tensor=True)
    job_emb = sbert_model.encode(list(job_skills), convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(resume_emb, job_emb).mean().item()
    return round(similarity * 50, 2)  # Scale to 50%

# Function to detect missing skills
def find_missing_skills(resume_skills, job_skills):
    return list(set(job_skills) - set(resume_skills))

# Function to generate feedback using TF-IDF
def generate_feedback(resume_text):
    if not resume_text.strip():
        return ["Your resume appears empty. Please add relevant content."]
    
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([resume_text])
        important_words = vectorizer.get_feature_names_out()

        feedback = []
        if len(important_words) < 10:
            feedback.append("Your resume lacks relevant keywords. Consider adding more industry-specific skills and achievements.")
        else:
            feedback.append("Your resume has a good number of keywords, but ensure they match the job description.")

        return feedback
    except Exception as e:
        return [f"Error generating feedback: {str(e)}"]

# Function to calculate final resume score
def calculate_score(resume_data, job_data):
    resume_text = resume_data.get("text", "")
    resume_skills = extract_skills(resume_text)
    job_skills = set(job_data.get("skills", []))
    
    skill_match = calculate_semantic_similarity(resume_skills, job_skills)
    
    resume_exp = resume_data.get("experience", 0)
    job_exp = job_data.get("min_experience", 2)
    experience_match = min(30, (resume_exp / job_exp) * 30) if job_exp else 30  # Cap at 30%
    
    education_match = 20 if resume_data.get("education", "").lower() in job_data.get("education", "").lower() else 0  
    
    return {
        "score": round(skill_match + experience_match + education_match, 2),
        "missing_skills": find_missing_skills(resume_skills, job_skills)
    }

# Function to score resume for all job roles
def score_resume(resume_data, job_roles):
    if not job_roles:
        return {"error": "No job descriptions available for scoring."}
    
    return {job: calculate_score(resume_data, job_roles[job]) for job in job_roles}

# Function to recommend top job matches
def recommend_jobs(resume_data, job_roles, top_n=3):
    if not job_roles:
        return {"error": "No job descriptions available for matching."}
    
    scores = {job: calculate_score(resume_data, job_roles[job])["score"] for job in job_roles}
    sorted_jobs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {"recommended_jobs": sorted_jobs[:top_n]}
