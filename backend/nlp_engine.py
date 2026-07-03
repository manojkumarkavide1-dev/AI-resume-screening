import PyPDF2
import docx
import re
import math
from collections import Counter

COMMON_SKILLS = [
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'react', 'angular', 'vue',
    'node.js', 'express', 'flask', 'django', 'spring', 'sql', 'mysql', 'postgresql', 'mongodb',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'html', 'css', 'git', 'machine learning',
    'deep learning', 'nlp', 'scikit-learn', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'linux',
    'rest api', 'graphql', 'nosql', 'agile', 'scrum', 'ci/cd', 'jenkins', 'github actions',
    'ruby', 'php', 'swift', 'kotlin', 'go', 'rust'
]

# Basic English stop words
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
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
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
    """Lowercase, remove punctuation, split into tokens, remove stop words."""
    tokens = re.findall(r'[a-z]+', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def _compute_tf(tokens):
    """Term frequency: count of each term / total terms."""
    count = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {term: freq / total for term, freq in count.items()}


def _cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two TF-IDF dicts."""
    # Dot product
    dot = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in vec_a)
    # Magnitudes
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

    # Build vocabulary from both documents
    all_tokens = set(tokens_jd) | set(tokens_resume)

    # TF for each doc
    tf_jd = _compute_tf(tokens_jd)
    tf_resume = _compute_tf(tokens_resume)

    # IDF (with two documents only)
    idf = {}
    for term in all_tokens:
        doc_count = (1 if term in tf_jd else 0) + (1 if term in tf_resume else 0)
        idf[term] = math.log((2 + 1) / (doc_count + 1)) + 1  # smooth IDF

    # TF-IDF vectors
    tfidf_jd = {term: tf_jd.get(term, 0) * idf[term] for term in all_tokens}
    tfidf_resume = {term: tf_resume.get(term, 0) * idf[term] for term in all_tokens}

    similarity = _cosine_similarity(tfidf_jd, tfidf_resume)
    return round(similarity * 100, 2)
