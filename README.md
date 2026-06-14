# resume-jd-matcher
# AI Resume & JD Matcher

An AI-powered application that analyzes how well a resume matches a job description using Natural Language Processing (NLP), semantic similarity, keyword analysis, and Large Language Models (LLMs).

#OVERVIEW:
This project helps automate the process of tailoring your resume to a specific job description by comparing a resume with a job description and providing:

*  Overall Match Score
*  Missing Keywords & Skills
*  Matching Skills Analysis
*  Semantic Similarity Evaluation
*  AI-Generated Resume Improvement Suggestions

The goal is to help job seekers optimize their resumes and improve their chances of passing Applicant Tracking Systems (ATS).

---

# FEATURES

## Resume Upload

* Upload resumes in PDF or text format.
* Automatic text extraction and preprocessing.

## Job Description Analysis

* Paste any job description.
* Extract important skills, technologies, and role-specific keywords.

## Semantic Matching

* Uses Sentence-BERT embeddings to understand contextual similarity.
* Calculates cosine similarity between resume and job description.

## Keyword Gap Analysis

* Identifies missing skills and keywords.
* Highlights overlapping competencies.

## AI-Powered Suggestions

* Generates actionable recommendations to improve resume relevance.
* Suggests skill additions, project improvements, and keyword optimization.

## Interactive Dashboard

* Match score visualization.
* Matched skills section.
* Missing keywords section.
* Resume enhancement recommendations.

---

# SYSTEM ARCHITECTURE

```text
Resume Upload + Job Description
            │
            ▼
    Text Extraction Layer
     (PyMuPDF / PDF Parser)
            │
            ▼
      Text Preprocessing
    (Cleaning & Normalization)
            │
            ▼
      NLP Matching Engine
    (Sentence-BERT Embeddings)
            │
            ▼
      Cosine Similarity Score
            │
            ├────────► Match Percentage
            │
            ▼
     Keyword Extraction Layer
      (spaCy + TF-IDF)
            │
            ├────────► Matched Skills
            └────────► Missing Keywords
            │
            ▼
       LLM Suggestions
    (GPT / Gemini API)
            │
            ▼
      Results Dashboard
```

---

# TECH STACK

### Frontend

* Streamlit
* React (Optional Alternative)

### Backend

* Python

### NLP & AI

* Sentence-BERT
* spaCy
* TF-IDF
* Cosine Similarity
* OpenAI GPT / Google Gemini API

### Document Processing

* PyMuPDF

### Deployment

* Streamlit Cloud
* Hugging Face Spaces

---

# 📂 PROJECT STRUCTURE

```text
AI-Resume-JD-Matcher/
│
├── app.py
├── requirements.txt
├── utils/
│   ├── pdf_parser.py
│   ├── preprocessing.py
│   ├── matcher.py
│   ├── keyword_extractor.py
│   └── suggestions.py
│
├── assets/
├── sample_data/
│
├── README.md
└── .gitignore
```

---

# INSTALLATION

### Clone the Repository

```bash
git clone https://github.com/your-username/AI-Resume-JD-Matcher.git

cd AI-Resume-JD-Matcher
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

The application will launch in your browser.

---

## 📊 How It Works

### Step 1

Upload your resume (PDF/Text).

### Step 2

Paste the target job description.

### Step 3

The system:

* Extracts resume text
* Cleans and preprocesses content
* Generates embeddings
* Calculates similarity score
* Extracts important keywords
* Identifies skill gaps
* Generates improvement suggestions

### Step 4

View results in an interactive dashboard.

---

# Example Output

```text
Overall Match Score: 78%

Matched Skills:
✔ Python
✔ SQL
✔ Machine Learning
✔ Data Analysis

Missing Keywords:
✖ Docker
✖ Kubernetes
✖ AWS

AI Suggestions:
• Add cloud-related projects.
• Highlight deployment experience.
• Include Docker and Kubernetes skills where applicable.
```

---

# Use Cases

* Resume Optimization
* ATS Readiness Check
* Career Guidance
* Skill Gap Analysis
* Job Application Preparation

---

# Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---
