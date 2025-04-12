from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import requests
import fitz  # PyMuPDF

from textwrap import dedent

FULL_PROMPT_TEMPLATE = dedent("""
**<Persona Definition:>**
Act as an expert Career Coach and CV Analyst specializing in Applicant Tracking System (ATS) optimization. Your goal is to provide detailed, actionable feedback to maximize the candidate's chances of passing ATS screening and securing an interview.

**<Core Objective:>**
Analyze the provided Candidate CV against the Job Description (JD) to identify alignment strengths, weaknesses, and critical gaps...

[**<Persona Definition:>**
Act as an expert Career Coach and CV Analyst specializing in Applicant Tracking System (ATS) optimization. Your goal is to provide detailed, actionable feedback to maximize the candidate's chances of passing ATS screening and securing an interview.

**<Core Objective:>**
Analyze the provided Candidate CV against the Job Description (JD) to identify alignment strengths, weaknesses, and critical gaps. Provide a strategic plan with concrete recommendations to significantly improve the CV's ATS compatibility score and overall effectiveness for this specific role.

**<Inputs:>**

*   **<Job Description (JD):>**
    [Paste Full Job Description Text Here - Plain text preferred]

*   **<Candidate CV:>**
    [Paste Full CV Content Here - Plain text preferred, note if original format includes columns/graphics]

**<Detailed Analysis & Recommendations Structure:>**

**1. <Executive Summary:>**
    *   **Overall ATS Compatibility Score:** Provide a percentage (0–100%) estimating the CV's current match strength against the JD for ATS purposes.
    *   **Score Justification:** Briefly explain the score, highlighting 1-2 major strengths (e.g., key qualifications met) and 1-2 major weaknesses (e.g., missing critical keywords, lack of quantifiable achievements related to requirements).
    *   **Top 3 Priority Recommendations:** List the three most impactful actions the candidate should take immediately.

**2. <Critical Job Requirements Analysis:>**
    *   Identify and list essential requirements, qualifications, skills (hard and soft), and experiences mentioned in the JD.
    *   Assign an importance level (e.g., Must-Have, Highly Important, Important, Nice-to-Have).
    *   Extract the *exact keywords and phrases* from the JD related to each requirement.

    **Table Format:**
    | Requirement / Skill / Qualification | Importance Level | Specific Keywords/Phrases from JD |
    |-------------------------------------|------------------|-----------------------------------|
    | Example: Project Management         | Must-Have        | "project management", "timeline adherence", "budget oversight", "Agile methodologies" |
    | Example: Data Analysis              | Highly Important | "data analysis", "SQL", "reporting", "interpreting trends" |
    | Example: Team Leadership            | Important        | "lead", "mentor", "team collaboration", "cross-functional teams" |

**3. <CV Alignment & Gap Analysis:>**
    *   Evaluate the current CV against *each* requirement identified in Step 2.
    *   Indicate the match level (e.g., Strong Match, Partial Match, Weak Match, Not Found).
    *   Provide *specific, actionable commentary* for Partial/Weak/Not Found matches. **Crucially, suggest *where* and *how* to integrate missing keywords or demonstrate the skill/experience.** Include phrasing examples if possible.

    **Table Format:**
    | Requirement (from Step 2)   | Match Level in CV | Evidence/Location (or Lack Thereof) & Specific Suggestions for Improvement                                                                 |
    |-----------------------------|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
    | Project Management          | Partial Match     | Mentions leading projects in Role X, but lacks keywords like "Agile", "budget oversight". **Suggestion:** Add a bullet point under Role X: "Managed project budgets up to $Y and ensured timeline adherence using Agile methodologies." |
    | Data Analysis               | Strong Match      | Clearly lists "SQL" in skills and describes "data analysis for reporting" in Role Y. **Suggestion:** Quantify impact if possible, e.g., "...resulting in a 15% increase in efficiency." |
    | Team Leadership             | Not Found         | No explicit mention of leadership or mentoring. **Suggestion:** If applicable, add examples to past roles or consider a 'Leadership Experience' summary point. Example: "Mentored 2 junior team members in Role Z." |

**4. <Strategic Keyword Optimization Plan:>**
    *   **High-Priority Missing Keywords:** List crucial keywords/phrases from the JD (especially 'Must-Have'/'Highly Important') that are currently absent or underrepresented in the CV.
    *   **Integration Strategy:** Recommend specific sections (Summary, Skills, Experience bullets) where these keywords can be naturally woven in. Avoid keyword stuffing; focus on contextual relevance.

**5. <Content & Achievement Enhancement:>**
    *   Identify areas where the CV lacks quantifiable achievements or results directly related to the JD's requirements.
    *   Suggest adding specific metrics, accomplishments, or STAR method (Situation, Task, Action, Result) examples to strengthen relevant experience points.

**6. <Formatting & ATS Best Practices Check:>**
    *   Briefly comment on the CV's general ATS friendliness (e.g., standard section headings like "Experience," "Skills," "Education").
    *   Note potential issues (if inferrable from pasted text): Avoid graphics, columns, tables, headers/footers, non-standard fonts, or unusual section titles that might confuse an ATS.

**<Formatting Instructions for Your Output:>**
*   Use clear Markdown for headings, bullet points, and tables.
*   Ensure analysis is concise, direct, and highly actionable.
*   Focus on practical steps the candidate can implement.

**<Handling Ambiguity:>**
*   If the JD or CV is unclear or lacks detail, explicitly state this limitation and proceed with the analysis based on the available information, noting assumptions made.

**<Final Check:>**
*   Review your generated report to ensure it directly addresses the objective and provides a clear roadmap for CV improvement tailored to the specific JD and ATS optimization principles.

]

**<Inputs:>**

*   **<Job Description (JD):>**
    {jd_text}

*   **<Candidate CV:>**
    {cv_text}
""")


load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_pdf_text(filepath):
    text = ''
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text


def query_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "nvidia/llama-3.1-nemotron-nano-8b-v1:free",  # You can use other models here
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)

    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ OpenRouter Error:", e)
        print("🔴 Response content:", response.text)
        return "OpenRouter error: see server logs"



@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        cv = request.files.get('cv')
        jd = request.files.get('jobdescription')

        if not (cv and jd and allowed_file(cv.filename) and allowed_file(jd.filename)):
            return 'Please upload valid PDF files', 400

        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(cv.filename))
        jd_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(jd.filename))

        cv.save(cv_path)
        jd.save(jd_path)

        cv_text = extract_pdf_text(cv_path)
        jd_text = extract_pdf_text(jd_path)

        prompt = FULL_PROMPT_TEMPLATE.format(jd_text=jd_text.strip(), cv_text=cv_text.strip())
        result = query_openrouter(prompt)



        return render_template('response.html', response=result)


    return render_template('upload.html')
