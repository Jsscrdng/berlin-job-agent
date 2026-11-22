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

def evaluate_match(
    job_title: str, 
    job_description: str, 
    profile: Dict[str, Any] = None,
    target_location: str = "Berlin",
    primary_techs: List[str] = None
) -> Dict[str, Any]:
    if profile is None:
        profile = load_master_profile()
    if primary_techs is None:
        primary_techs = ["ruby", "rails"]
    
    text = f"{job_title} {job_description}".lower()
    
    # Specific high-value technical keywords to detect
    key_techs = [
        "ruby", "rails", "ruby on rails", "postgresql", "postgres", "sql", "aws", "docker", 
        "react", "reactjs", "python", "redis", "rspec", "ci/cd", "rest", "api", "graphql", 
        "microservices", "kubernetes", "cloud", "agile", "scrum", "tdd"
    ]
    
    matching_skills = []
    for skill in key_techs:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            matching_skills.append(skill.title())
    
    # Dynamic primary tech match
    has_primary = any(t.lower() in text for t in primary_techs)
    
    score = 50.0  # Base for role alignment
    if has_primary:
        score += 30.0
    if any(db in text for db in ["postgresql", "postgres", "sql"]):
        score += 10.0
    if any(cl in text for cl in ["aws", "cloud", "docker"]):
        score += 5.0
    if "react" in text or "python" in text:
        score += 5.0
        
    score = min(100.0, score)
    
    lang = detect_language(job_description)
    loc_clean = target_location.lower().strip()
    is_location_match = (loc_clean in text) or ("remote" in text) or ("deutschland" in text)
    
    return {
        "match_score": round(score, 1),
        "language": lang,
        "matching_skills": list(set(matching_skills)),
        "is_location_match": is_location_match,
        "is_qualified": score >= 70.0 and is_location_match
    }
