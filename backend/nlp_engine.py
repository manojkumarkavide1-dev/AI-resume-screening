import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

COMMON_SKILLS = [
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'react', 'angular', 'vue', 
    'node.js', 'express', 'flask', 'django', 'spring', 'sql', 'mysql', 'postgresql', 'mongodb',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'html', 'css', 'git', 'machine learning',
    'deep learning', 'nlp', 'scikit-learn', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'linux',
    'rest api', 'graphql', 'nosql', 'agile', 'scrum', 'ci/cd', 'jenkins', 'github actions',
    'ruby', 'php', 'swift', 'kotlin', 'go', 'rust'
]

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
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def extract_skills(text):
    text_lower = text.lower()
    found_skills = []
    for skill in COMMON_SKILLS:
        # Regex to find exact word match, handling special chars
        # For skills like 'c++', \b might not work perfectly because + is not a word character.
        # But for simplicity, we do a basic find.
        # Let's adjust pattern: pad with spaces or punctuation checking.
        pattern = r'(?<![a-z0-9])' + re.escape(skill) + r'(?![a-z0-9])'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())
    return found_skills

def calculate_match(resume_text, job_description):
    if not resume_text.strip() or not job_description.strip():
        return 0.0
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([job_description, resume_text])
    
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    return round(float(similarity) * 100, 2)
