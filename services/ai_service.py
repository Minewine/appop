"""
AI service module for interacting with OpenRouter API.
"""
import os
import requests
import json
import hashlib
from flask import current_app
from config import Config, FULL_PROMPT_TEMPLATE_EN, FULL_PROMPT_TEMPLATE_FR
from services.mock_ai_service import get_mock_analysis
from services.pdf_service import extract_cv_sections, extract_jd_requirements
from functools import lru_cache

def get_cache_key(text, prompt_type, lang):
    """Generate a cache key for AI requests"""
    # Use a hash of the input to create a unique key
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return f"ai_analysis:{prompt_type}:{lang}:{text_hash}"

def query_openrouter(text, prompt_type="ats_cv_analysis", lang="en"):
    """
    Query the OpenRouter API for AI analysis
    
    Args:
        text: Text to analyze
        prompt_type: Type of analysis to perform
        lang: Language for analysis (en/fr)
        
    Returns:
        str: Analysis result
    """
    try:
        current_app.logger.info(f"Performing {prompt_type} analysis on text ({len(text)} chars)")
        
        # Check for empty text
        if not text or len(text) < 10:
            current_app.logger.error("Text is too short for analysis")
            return "Error: The provided text is too short for meaningful analysis."
        
        # Check if we should use mock service (based on config or environment)
        use_mock = current_app.config.get('USE_MOCK_AI', False)
        
        if use_mock:
            return get_mock_analysis(prompt_type, lang)
            
        # Check cache for existing result
        cache = current_app.extensions.get('cache')
        if cache:
            cache_key = get_cache_key(text, prompt_type, lang)
            cached_result = cache.get(cache_key)
            if cached_result:
                current_app.logger.info(f"Returning cached analysis result")
                return cached_result
        
        # Enhance analysis with document structure extraction if feature is enabled
        structured_context = ""
        if prompt_type == "ats_cv_analysis" and current_app.config.get('FEATURE_ADVANCED_CV_PARSING', False):
            try:
                cv_sections = extract_cv_sections(text)
                if cv_sections:
                    structured_context = "\nCV Structure Analysis:\n"
                    for section_name, section_data in cv_sections.items():
                        structured_context += f"- Section: {section_data['header']}\n"
            except Exception as e:
                current_app.logger.warning(f"Error extracting CV structure: {e}")
        
        # Select template based on language
        template = FULL_PROMPT_TEMPLATE_FR if lang == "fr" else FULL_PROMPT_TEMPLATE_EN
            
        # Determine which prompt to use based on prompt_type
        if prompt_type == "ats_cv_analysis":
            # For CV-only analysis, use the same template but with a placeholder JD
            placeholder_jd = "This is a general CV analysis without a specific job description."
            prompt = template.format(
                cv_text=text[:5000],
                jd_text=placeholder_jd
            )
            # Add structured context if available
            if structured_context:
                prompt += f"\n\nAdditional Context: {structured_context}"
        else:
            # For any other analysis, use a more generic prompt
            prompt = f"Analyze the following text: {text[:7500]}"
        
        # OpenRouter API endpoint and parameters
        api_url = current_app.config.get('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
        api_key = current_app.config.get('OPENROUTER_API_KEY', '')
        
        if not api_key:
            current_app.logger.error("OpenRouter API key is missing")
            return get_mock_analysis(prompt_type, lang)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://appop-demo.com",  # You should update this to your domain
            "X-Title": "AppOp CV Analysis"
        }
        
        payload = {
            "model": current_app.config.get('DEFAULT_MODEL', 'meta-llama/llama-3-8b-instruct'),
            "messages": [
                {"role": "system", "content": "You are an expert CV analyst specializing in ATS optimization."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        current_app.logger.info(f"Sending request to OpenRouter API with model: {payload['model']}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            current_app.logger.info(f"Received response from OpenRouter API: {len(content)} chars")
            
            # Cache the result if cache is available
            if cache and content:
                cache.set(cache_key, content, timeout=current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))
                
            return content
        else:
            current_app.logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            # Fall back to mock service when API request fails
            return get_mock_analysis(prompt_type, lang)
            
    except Exception as e:
        current_app.logger.error(f"Error querying OpenRouter API: {e}")
        # Fall back to mock service on exception
        return get_mock_analysis(prompt_type, lang)

def analyze_cv_with_jd(cv_text, jd_text, lang="en"):
    """
    Analyze CV against job description using AI
    
    Args:
        cv_text: CV text content
        jd_text: Job description text content
        lang: Language for analysis (en/fr)
        
    Returns:
        str: Analysis result comparing CV to job description
    """
    try:
        current_app.logger.info(f"Starting CV-JD analysis in {lang}")
        
        # Check if we should use mock service (based on config or environment)
        use_mock = current_app.config.get('USE_MOCK_AI', False)
        
        if use_mock:
            return get_mock_analysis("cv_jd_match", lang)
            
        # Check cache for existing result
        cache = current_app.extensions.get('cache')
        if cache:
            # Create a unique key based on both CV and JD content
            combined_text = f"{cv_text[:1000]}{jd_text[:1000]}"
            cache_key = get_cache_key(combined_text, "cv_jd_match", lang)
            cached_result = cache.get(cache_key)
            if cached_result:
                current_app.logger.info(f"Returning cached CV-JD analysis result")
                return cached_result
        
        # Enhanced analysis with document structure extraction if feature is enabled
        enhanced_context = ""
        if current_app.config.get('FEATURE_JOB_REQUIREMENTS_EXTRACTION', False):
            try:
                # Extract structured JD requirements
                jd_requirements = extract_jd_requirements(jd_text)
                cv_sections = extract_cv_sections(cv_text)
                
                if jd_requirements and any(reqs for reqs in jd_requirements.values()):
                    enhanced_context += "\nStructured Job Requirements:\n"
                    for category, reqs in jd_requirements.items():
                        if reqs:
                            enhanced_context += f"- {category.replace('_', ' ').title()}:\n"
                            for req in reqs[:5]:  # Limit to top 5 items per category
                                enhanced_context += f"  * {req}\n"
                
                if cv_sections:
                    enhanced_context += "\nCV Structure:\n"
                    for section_name, section_data in cv_sections.items():
                        enhanced_context += f"- Section: {section_data['header']}\n"
            except Exception as e:
                current_app.logger.warning(f"Error extracting structured data: {e}")
        
        # Select template based on language
        template = FULL_PROMPT_TEMPLATE_FR if lang == "fr" else FULL_PROMPT_TEMPLATE_EN
        
        # Format the prompt with CV and JD text
        # Truncate texts to avoid exceeding token limits
        prompt = template.format(
            cv_text=cv_text[:5000],
            jd_text=jd_text[:3000]
        )
        
        # Add enhanced context if available
        if enhanced_context:
            prompt += f"\n\nAdditional Structured Analysis:\n{enhanced_context}"
        
        # OpenRouter API endpoint and parameters
        api_url = current_app.config.get('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
        api_key = current_app.config.get('OPENROUTER_API_KEY', '')
        
        if not api_key:
            current_app.logger.error("OpenRouter API key is missing")
            return get_mock_analysis("cv_jd_match", lang)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://appop-demo.com",  # Update to your domain
            "X-Title": "AppOp CV-JD Analysis"
        }
        
        payload = {
            "model": current_app.config.get('DEFAULT_MODEL', 'meta-llama/llama-3-8b-instruct'),
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        current_app.logger.info(f"Sending CV-JD analysis request with {len(cv_text)} chars CV and {len(jd_text)} chars JD")
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            current_app.logger.info(f"Received CV-JD analysis response: {len(content)} chars")
            
            # Cache the result if cache is available
            if cache and content:
                cache.set(cache_key, content, timeout=current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300))
                
            return content
        else:
            current_app.logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            # Fall back to mock service when API request fails
            return get_mock_analysis("cv_jd_match", lang)
            
    except Exception as e:
        current_app.logger.error(f"Error in CV-JD analysis: {e}")
        # Fall back to mock service on exception
        return get_mock_analysis("cv_jd_match", lang)

def get_keyword_match_score(cv_text, jd_text):
    """
    Calculate a simple keyword match score between CV and job description
    
    Args:
        cv_text: CV text content
        jd_text: Job description text content
        
    Returns:
        dict: Match score data including percentage and matched keywords
    """
    try:
        # Extract requirements from job description
        jd_requirements = extract_jd_requirements(jd_text)
        
        # Create a list of all keywords from requirements
        all_keywords = []
        for category, requirements in jd_requirements.items():
            if category != 'other':  # Skip generic requirements
                for req in requirements:
                    # Split requirement into individual words and filter out common words
                    words = [w.lower() for w in req.split() if len(w) > 3 and w.lower() not in COMMON_WORDS]
                    all_keywords.extend(words)
                    
                    # Also add multi-word technical terms
                    # This is a simplistic approach; more advanced NLP would be better
                    for i in range(len(words) - 1):
                        all_keywords.append(f"{words[i]} {words[i+1]}")
        
        # Remove duplicates and sort
        all_keywords = sorted(list(set(all_keywords)))
        
        # Count matches in CV
        matched_keywords = []
        cv_text_lower = cv_text.lower()
        
        for keyword in all_keywords:
            if keyword in cv_text_lower:
                matched_keywords.append(keyword)
        
        # Calculate match percentage
        match_percentage = 0
        if all_keywords:
            match_percentage = round((len(matched_keywords) / len(all_keywords)) * 100, 1)
        
        return {
            'match_percentage': match_percentage,
            'matched_keywords': matched_keywords,
            'total_keywords': len(all_keywords),
            'matches_found': len(matched_keywords)
        }
    
    except Exception as e:
        current_app.logger.error(f"Error calculating keyword match score: {e}")
        return {
            'match_percentage': 0,
            'matched_keywords': [],
            'total_keywords': 0,
            'matches_found': 0,
            'error': str(e)
        }

# List of common words to exclude from keyword matching
COMMON_WORDS = {
    'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this',
    'but', 'his', 'from', 'they', 'she', 'will', 'say', 'would', 'been', 
    'each', 'can', 'their', 'more', 'about', 'into', 'than', 'them', 'then',
    'these', 'some', 'such', 'what', 'when', 'make', 'like', 'time', 'just',
    'year', 'only', 'also', 'work', 'over', 'very', 'even', 'most', 'take',
    'experience', 'role', 'team', 'position', 'candidate', 'job', 'company',
    'responsibilities', 'requirements'
}