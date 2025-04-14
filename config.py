import os
from textwrap import dedent  # Use textwrap.dedent instead of importing dedent directly

class Config:
    """Configuration for the Flask application"""
    # Secret key for session security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-testing-only-change-in-production')
    
    # Upload configurations
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # API configurations
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
    
    # Default model configuration
    DEFAULT_MODEL = 'meta-llama/llama-3-8b-instruct'
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    
    # Enhanced database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///appop_demo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    MIGRATE_JSON_TO_DB = True  # Set to False after first run
    
    # Admin user configuration
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@appop-demo.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123!')  # Change in production!
    
    # Cache configuration
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Security settings
    PASSWORD_SALT = os.getenv('PASSWORD_SALT', 'default-salt-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', SECRET_KEY)
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # API rate limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STRATEGY = "fixed-window"
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_HEADER_LIMIT = "X-RateLimit-Limit"
    RATELIMIT_HEADER_REMAINING = "X-RateLimit-Remaining"
    RATELIMIT_HEADER_RESET = "X-RateLimit-Reset"
    RATELIMIT_SWALLOW_ERRORS = False
    
    # API rate limits by endpoint
    RATELIMIT_APPLICATION_LIMITS = {
        "analyze_cv": "20/day;5/hour",  # Analysis is resource-intensive
        "upload_file": "50/day;10/hour",
        "login": "10/minute",  # Prevent brute-force login attempts
        "register": "5/hour",   # Prevent spam registrations
    }
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' cdnjs.cloudflare.com cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' fonts.googleapis.com cdnjs.cloudflare.com 'unsafe-inline'; font-src 'self' fonts.gstatic.com; img-src 'self' data:;"
    }
    
    # Login security
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 30
    
    # Feature flags
    FEATURE_ADVANCED_CV_PARSING = True
    FEATURE_JOB_REQUIREMENTS_EXTRACTION = True
    FEATURE_CV_JD_COMPARISON_CHART = True
    
    # PDF processing settings
    PDF_EXTRACT_IMAGES = False
    PDF_OCR_ENABLED = False  # Enable if you add OCR capability
    APPLICATION_ROOT = '/appop'

# Prompt templates
# English Version
FULL_PROMPT_TEMPLATE_EN = dedent("""
**<Persona Definition:>**
Act as an expert Career Coach and CV Analyst specializing in Applicant Tracking System (ATS) optimization. Your goal is to provide detailed, actionable feedback to maximize the candidate's chances of passing ATS screening and securing an interview.

**<Core Objective:>**
Analyze the provided Candidate CV against the Job Description (JD) to identify alignment strengths, weaknesses, and critical gaps. Provide a strategic plan with concrete recommendations to significantly improve the CV's ATS compatibility score and overall effectiveness for this specific role.

**<Inputs:>**

*   **<Job Description (JD):>**
    {jd_text}

*   **<Candidate CV:>**
    {cv_text}

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
""")

# French Version
FULL_PROMPT_TEMPLATE_FR = dedent("""
**<Définition de la Persona :>**
Agissez en tant que Coach de Carrière expert et Analyste de CV spécialisé dans l'optimisation pour les Applicant Tracking Systems (ATS). Votre objectif est de fournir un retour détaillé et exploitable pour maximiser les chances du candidat de passer le filtrage ATS et de décrocher un entretien.

**<Objectif Principal :>**
Analysez le CV du candidat fourni par rapport à la Description de Poste (DP) pour identifier les points forts de l'alignement, les faiblesses et les lacunes critiques. Fournissez un plan stratégique avec des recommandations concrètes pour améliorer significativement le score de compatibilité ATS du CV et son efficacité globale pour ce poste spécifique.

**<Entrées :>**

*   **<Description de Poste (DP) :>**
    {jd_text}

*   **<CV du Candidat :>**
    {cv_text}

**<Structure d'Analyse Détaillée & Recommandations :>**

**1. <Résumé Exécutif :>**
    *   **Score Global de Compatibilité ATS :** Fournissez un pourcentage (0–100 %) estimant la force de correspondance actuelle du CV par rapport à la DP pour les besoins de l'ATS.
    *   **Justification du Score :** Expliquez brièvement le score, en soulignant 1-2 points forts majeurs (ex : qualifications clés satisfaites) et 1-2 faiblesses majeures (ex : mots-clés critiques manquants, manque de réalisations quantifiables liées aux exigences).
    *   **Top 3 des Recommandations Prioritaires :** Listez les trois actions les plus impactantes que le candidat devrait entreprendre immédiatement.

**2. <Analyse des Exigences Clés du Poste :>**
    *   Identifiez et listez les exigences essentielles, qualifications, compétences (techniques et comportementales) et expériences mentionnées dans la DP.
    *   Attribuez un niveau d'importance (ex : Indispensable, Très Important, Important, Atout).
    *   Extrayez les *mots-clés et phrases exacts* de la DP liés à chaque exigence.

    **Format Tableau :**
    | Exigence / Compétence / Qualification | Niveau d'Importance | Mots-clés/Phrases Spécifiques de la DP |
    |---------------------------------------|---------------------|----------------------------------------|
    | Exemple : Gestion de Projet           | Indispensable       | "gestion de projet", "respect des délais", "supervision budgétaire", "méthodologies Agile" |
    | Exemple : Analyse de Données          | Très Important      | "analyse de données", "SQL", "reporting", "interprétation des tendances" |
    | Exemple : Leadership d'Équipe         | Important           | "diriger", "mentor", "collaboration d'équipe", "équipes interfonctionnelles" |

**3. <Analyse de l'Alignement et des Lacunes du CV :>**
    *   Évaluez le CV actuel par rapport à *chaque* exigence identifiée à l'Étape 2.
    *   Indiquez le niveau de correspondance (ex : Forte Correspondance, Correspondance Partielle, Faible Correspondance, Non Trouvé).
    *   Fournissez des *commentaires spécifiques et exploitables* pour les correspondances Partielles/Faibles/Non Trouvées. **Suggérez de manière cruciale *où* et *comment* intégrer les mots-clés manquants ou démontrer la compétence/expérience.** Incluez des exemples de formulation si possible.

    **Format Tableau :**
    | Exigence (de l'Étape 2)       | Niveau de Correspondance dans le CV | Preuve/Emplacement (ou Absence) & Suggestions Spécifiques d'Amélioration                                                                                             |
    |-------------------------------|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | Gestion de Projet             | Correspondance Partielle            | Mentionne la direction de projets dans le Rôle X, mais manque de mots-clés comme "Agile", "supervision budgétaire". **Suggestion :** Ajouter une puce sous le Rôle X : "Gestion de budgets de projet jusqu'à Y$ et respect des délais en utilisant les méthodologies Agile." |
    | Analyse de Données            | Forte Correspondance                | Liste clairement "SQL" dans les compétences et décrit "l'analyse de données pour le reporting" dans le Rôle Y. **Suggestion :** Quantifier l'impact si possible, ex : "...résultant en une augmentation de 15% de l'efficacité." |
    | Leadership d'Équipe           | Non Trouvé                          | Aucune mention explicite de leadership ou de mentorat. **Suggestion :** Si applicable, ajouter des exemples aux rôles passés ou envisager un point résumé 'Expérience en Leadership'. Exemple : "Mentoré 2 membres juniors de l'équipe dans le Rôle Z." |

**4. <Plan Stratégique d'Optimisation des Mots-clés :>**
    *   **Mots-clés Manquants Hautement Prioritaires :** Listez les mots-clés/phrases cruciaux de la DP (surtout 'Indispensable'/'Très Important') qui sont actuellement absents ou sous-représentés dans le CV.
    *   **Stratégie d'Intégration :** Recommandez des sections spécifiques (Résumé, Compétences, Puces d'Expérience) où ces mots-clés peuvent être intégrés naturellement. Évitez le bourrage de mots-clés ; concentrez-vous sur la pertinence contextuelle.

**5. <Amélioration du Contenu & des Réalisations :>**
    *   Identifiez les domaines où le CV manque de réalisations quantifiables ou de résultats directement liés aux exigences de la DP.
    *   Suggérez d'ajouter des métriques spécifiques, des accomplissements ou des exemples selon la méthode STAR (Situation, Tâche, Action, Résultat) pour renforcer les points d'expérience pertinents.

**6. <Vérification du Formatage & des Bonnes Pratiques ATS :>**
    *   Commentez brièvement la compatibilité générale du CV avec les ATS (ex : titres de section standards comme "Expérience," "Compétences," "Formation").
    *   Notez les problèmes potentiels (si déductibles du texte collé) : Évitez les graphiques, colonnes, tableaux, en-têtes/pieds de page, polices non standard ou titres de section inhabituels qui pourraient perturber un ATS.

**<Instructions de Formatage pour Votre Réponse :>**
*   Utilisez du Markdown clair pour les titres, les puces et les tableaux.
*   Assurez-vous que l'analyse est concise, directe et hautement exploitable.
*   Concentrez-vous sur les étapes pratiques que le candidat peut mettre en œuvre.

**<Gestion de l'Ambiguïté :>**
*   Si la DP ou le CV n'est pas clair ou manque de détails, énoncez explicitement cette limitation et procédez à l'analyse sur la base des informations disponibles, en notant les hypothèses faites.

**<Vérification Finale :>**
*   Relisez votre rapport généré pour vous assurer qu'il répond directement à l'objectif et fournit une feuille de route claire pour l'amélioration du CV adaptée à la DP spécifique et aux principes d'optimisation ATS.
""")
