"""
Single-file Vercel serverless entrypoint.
Combines models, nlp_engine, and app into one file to avoid cross-directory import issues.
"""

import os
import io
import re
import math
from collections import Counter

import PyPDF2
import docx
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, String, Float, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
Base = declarative_base()


class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    filename = Column(String(255), nullable=False)
    resume_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)
    match_score = Column(Float, default=0.0)
    skills = Column(String(500), default="")  # Comma separated skills


DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # On Vercel the filesystem is read-only except /tmp
    db_path = "sqlite:////tmp/resumes.db" if os.environ.get("VERCEL") else "sqlite:///resumes.db"
    engine = create_engine(db_path, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# NLP ENGINE (pure Python — no numpy/scipy)
# ─────────────────────────────────────────────
COMMON_SKILLS = [
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'react', 'angular', 'vue',
    'node.js', 'express', 'flask', 'django', 'spring', 'sql', 'mysql', 'postgresql', 'mongodb',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'html', 'css', 'git', 'machine learning',
    'deep learning', 'nlp', 'scikit-learn', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'linux',
    'rest api', 'graphql', 'nosql', 'agile', 'scrum', 'ci/cd', 'jenkins', 'github actions',
    'ruby', 'php', 'swift', 'kotlin', 'go', 'rust'
]

STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'shall', 'can', 'not', 'no', 'nor', 'so', 'yet', 'both',
    'either', 'neither', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'than', 'too', 'very', 'just', 'as', 'if', 'then', 'that', 'this', 'it',
    'its', 'we', 'our', 'you', 'your', 'he', 'she', 'they', 'their', 'i', 'my'
}


def extract_text_from_pdf(file_stream):
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def extract_text_from_docx(file_stream):
    try:
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""


def extract_skills(text):
    text_lower = text.lower()
    found_skills = []
    for skill in COMMON_SKILLS:
        pattern = r'(?<![a-z0-9])' + re.escape(skill) + r'(?![a-z0-9])'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())
    return found_skills


def _tokenize(text):
    tokens = re.findall(r'[a-z]+', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def _compute_tf(tokens):
    count = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {term: freq / total for term, freq in count.items()}


def _cosine_similarity(vec_a, vec_b):
    dot = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in vec_a)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def calculate_match(resume_text, job_description):
    if not resume_text.strip() or not job_description.strip():
        return 0.0
    tokens_jd = _tokenize(job_description)
    tokens_resume = _tokenize(resume_text)
    all_tokens = set(tokens_jd) | set(tokens_resume)
    tf_jd = _compute_tf(tokens_jd)
    tf_resume = _compute_tf(tokens_resume)
    idf = {}
    for term in all_tokens:
        doc_count = (1 if term in tf_jd else 0) + (1 if term in tf_resume else 0)
        idf[term] = math.log((2 + 1) / (doc_count + 1)) + 1
    tfidf_jd = {term: tf_jd.get(term, 0) * idf[term] for term in all_tokens}
    tfidf_resume = {term: tf_resume.get(term, 0) * idf[term] for term in all_tokens}
    return round(_cosine_similarity(tfidf_jd, tfidf_resume) * 100, 2)


# ─────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/analyze', methods=['POST'])
def analyze_resumes():
    if 'job_description' not in request.form:
        return jsonify({"error": "Job description is required"}), 400

    job_description = request.form['job_description']

    if 'resumes' not in request.files:
        return jsonify({"error": "No resumes uploaded"}), 400

    files = request.files.getlist('resumes')

    if not files or files[0].filename == '':
        return jsonify({"error": "No selected files"}), 400

    db = SessionLocal()
    results = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            file_stream = io.BytesIO(file.read())

            if ext == 'pdf':
                resume_text = extract_text_from_pdf(file_stream)
            elif ext == 'docx':
                resume_text = extract_text_from_docx(file_stream)
            else:
                continue

            if not resume_text:
                continue

            match_score = calculate_match(resume_text, job_description)
            skills = extract_skills(resume_text)
            candidate_name = filename.rsplit('.', 1)[0].replace('_', ' ').title()

            candidate = Candidate(
                name=candidate_name,
                filename=filename,
                resume_text=resume_text,
                job_description=job_description,
                match_score=match_score,
                skills=",".join(skills)
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

            results.append({
                "id": candidate.id,
                "name": candidate.name,
                "filename": candidate.filename,
                "match_score": candidate.match_score,
                "skills": skills
            })

    db.close()
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(results)


@app.route('/api/results', methods=['GET'])
def get_results():
    db = SessionLocal()
    candidates = db.query(Candidate).order_by(Candidate.match_score.desc()).all()
    results = [{
        "id": c.id,
        "name": c.name,
        "filename": c.filename,
        "match_score": c.match_score,
        "skills": c.skills.split(",") if c.skills else []
    } for c in candidates]
    db.close()
    return jsonify(results)


@app.route('/api/results', methods=['DELETE'])
def clear_results():
    db = SessionLocal()
    try:
        db.query(Candidate).delete()
        db.commit()
        return jsonify({"message": "All results cleared"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data and data.get('username') == 'admin' and data.get('password') == 'admin123':
        return jsonify({"token": "admin-token-123", "role": "admin"}), 200
    return jsonify({"error": "Invalid credentials"}), 401


if __name__ == '__main__':
    app.run(debug=True, port=5000)
