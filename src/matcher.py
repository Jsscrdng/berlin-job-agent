import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

PROFILE_PATH = Path(__file__).resolve().parent.parent / "mi_perfil" / "perfil_maestro.json"

def load_master_profile() -> Dict[str, Any]:
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_language(text: str) -> str:
    german_indicators = ["wir suchen", "ihr profil", "aufgaben", "anforderungen", "kenntnisse", "deutsch", "berufserfahrung", "bewerbung"]
    lower = text.lower()
    de_count = sum(1 for word in german_indicators if word in lower)
    return "de" if de_count >= 2 else "en"

def evaluate_match(job_title: str, job_description: str, profile: Dict[str, Any] = None) -> Dict[str, Any]:
    if profile is None:
        profile = load_master_profile()
    
    text = f"{job_title} {job_description}".lower()
    
    # Flatten candidate skills
    all_skills = []
    for cat, skill_list in profile.get("technical_skills", {}).items():
        all_skills.extend(skill_list)
    
    # Specific high-value technical keywords to detect
    key_techs = [
        "ruby", "rails", "ruby on rails", "postgresql", "postgres", "sql", "aws", "docker", 
        "react", "reactjs", "python", "redis", "rspec", "ci/cd", "rest", "api", "graphql", 
        "microservices", "kubernetes", "cloud", "agile", "scrum", "tdd"
    ]
    
    matching_skills = []
    for skill in key_techs:
        # Match as whole word/phrase
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            matching_skills.append(skill.title())
    
    # Check core tech match
    has_rails = "ruby" in text or "rails" in text
    has_backend = "backend" in text or "fullstack" in text or "software" in text or "engineer" in text
    
    score = 50.0  # Base for software role
    if has_rails:
        score += 30.0
    if "postgresql" in text or "postgres" in text or "sql" in text:
        score += 10.0
    if "aws" in text or "cloud" in text:
        score += 5.0
    if "react" in text:
        score += 5.0
        
    score = min(100.0, score)
    
    lang = detect_language(job_description)
    
    return {
        "match_score": round(score, 1),
        "language": lang,
        "matching_skills": list(set(matching_skills)),
        "is_berlin": "berlin" in text or "remote" in text,
        "is_qualified": score >= 70.0
    }
