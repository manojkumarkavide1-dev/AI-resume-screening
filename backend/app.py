import os
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import init_db, SessionLocal, Candidate
from nlp_engine import extract_text_from_pdf, extract_text_from_docx, extract_skills, calculate_match

app = Flask(__name__)
# Enable CORS for the React frontend
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
            
            # Read file stream into memory
            file_stream = io.BytesIO(file.read())
            
            if ext == 'pdf':
                resume_text = extract_text_from_pdf(file_stream)
            elif ext == 'docx':
                resume_text = extract_text_from_docx(file_stream)
            else:
                continue
                
            if not resume_text:
                continue

            # NLP Processing
            match_score = calculate_match(resume_text, job_description)
            skills = extract_skills(resume_text)
            
            # Use filename without extension as candidate name temporarily
            candidate_name = filename.rsplit('.', 1)[0].replace('_', ' ').title()
            
            # Save to database
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
    
    # Sort results by score descending
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(results)

@app.route('/api/results', methods=['GET'])
def get_results():
    db = SessionLocal()
    candidates = db.query(Candidate).order_by(Candidate.match_score.desc()).all()
    
    results = []
    for c in candidates:
        results.append({
            "id": c.id,
            "name": c.name,
            "filename": c.filename,
            "match_score": c.match_score,
            "skills": c.skills.split(",") if c.skills else []
        })
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
    # Basic hardcoded admin check for prototype as requested
    if data and data.get('username') == 'admin' and data.get('password') == 'admin123':
        return jsonify({"token": "admin-token-123", "role": "admin"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
