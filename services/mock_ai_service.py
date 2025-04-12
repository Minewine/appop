"""
Mock AI service to use when OpenRouter API credits are exhausted.
This provides sample analysis responses for testing and demo purposes.
"""
import random
from flask import current_app
from datetime import datetime

# Sample CV analysis response
CV_ANALYSIS_SAMPLE = """
# CV Analysis Report

## ATS Compatibility Score: 78%

### Key Strengths
- Clear and professional formatting with consistent sections
- Good use of action verbs in experience descriptions
- Relevant skills are highlighted and aligned with industry standards
- Contact information is clearly presented at the top
- Professional summary effectively captures key qualifications

### Areas for Improvement
- Some industry-specific keywords could be more prominent
- Experience bullet points could be more quantifiable with metrics
- Education section could benefit from more details (GPA, relevant coursework)
- Skills section could be better organized by categories
- Some technical acronyms may not be recognized by all ATS systems

### Formatting Recommendations
1. **Section Headers**: Ensure all section headers are consistent in formatting
2. **Bullet Points**: Keep bullet points concise (1-2 lines each)
3. **Margins**: Maintain consistent margins (0.75"-1" recommended)
4. **Font**: Stick to ATS-friendly fonts (Arial, Calibri, Times New Roman)
5. **File Format**: Always submit as a standard PDF (as you've done)

### Keyword Optimization Suggestions
Based on industry standards, consider incorporating more of these keywords:
- Project management
- Strategic planning
- Cross-functional collaboration
- Data analysis
- Process optimization
- Client relationship management
- Budget oversight
- Performance metrics

### Final Recommendations
Your CV has a strong foundation but could benefit from more specific metrics and achievements. Consider adding numbers to quantify your achievements (e.g., "increased productivity by 25%") and tailoring keywords to specific job descriptions when applying.
"""

# Sample CV-JD match analysis response
CV_JD_MATCH_SAMPLE = """
# CV and Job Description Match Analysis

## Overall Match Score: 72%

### Key Matching Areas
| Requirement | Match | Notes |
|-------------|-------|-------|
| Technical Skills | 85% | Strong alignment in core technical competencies |
| Experience | 70% | Meets years of experience, industry context could be stronger |
| Education | 90% | Education requirements fully satisfied |
| Soft Skills | 65% | Some key soft skills present but could be emphasized more |
| Certifications | 50% | Some required certifications present, others missing |

### Strengths
1. Your technical expertise aligns well with the position's requirements
2. Education background is highly relevant to the role
3. Previous job titles and responsibilities show progression in relevant areas
4. Project experience demonstrates capability in required domains
5. Communication skills are well-evidenced throughout your experience

### Areas to Enhance
1. **Industry-Specific Experience**: The job requires more focus on {financial services/healthcare/technology} domain knowledge
2. **Leadership Experience**: The position emphasizes team leadership more than demonstrated in your CV
3. **Technical Tools**: Consider highlighting experience with {specific tools mentioned in JD}
4. **Certifications**: The role specifically requests {certification name} which isn't mentioned in your CV
5. **Project Scale**: Emphasize experience with larger-scale projects similar to what the role requires

### Keyword Alignment
The job description emphasizes these keywords that should be more prominent in your CV:
- Strategic planning
- Team leadership
- Budget management
- Stakeholder communication
- Risk assessment
- Performance optimization
- {Industry}-specific compliance

### Customization Recommendations
1. Revise your professional summary to better align with this specific role
2. Re-order your skills section to prioritize the most relevant skills for this position
3. Add specific metrics that demonstrate success in areas the job description emphasizes
4. Include more specific examples of projects similar to what would be expected in this role
5. Consider adding a brief statement about your knowledge of the company's industry

### Conclusion
Your CV shows good potential for this position with a 72% overall match. With targeted revisions focusing on the areas noted above, you could significantly strengthen your application. The strongest alignment is in your technical capabilities and education, while areas related to industry-specific experience and certain specialized skills would benefit from more emphasis or development.
"""

def get_mock_analysis(analysis_type="cv_only", lang="en"):
    """
    Returns a mock analysis result based on the analysis type.
    
    Args:
        analysis_type (str): Type of analysis ('cv_only' or 'cv_jd_match')
        lang (str): Language code ('en' or 'fr')
        
    Returns:
        str: Mock analysis result
    """
    current_app.logger.info(f"Using mock AI service for {analysis_type} analysis")
    
    # Add a small random delay to simulate API call
    # import time
    # time.sleep(random.uniform(1.5, 3.5))
    
    if analysis_type == "cv_jd_match":
        result = CV_JD_MATCH_SAMPLE
        if lang == "fr":
            # Note: In a real application, you would translate this properly
            result = "# Analyse de Correspondance CV et Description de Poste\n\n" + result
    else:
        result = CV_ANALYSIS_SAMPLE
        if lang == "fr":
            # Note: In a real application, you would translate this properly
            result = "# Rapport d'Analyse de CV\n\n" + result
    
    return result