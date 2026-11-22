import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
DRAFTS_DIR = BASE_DIR / "vacantes_para_enviar"

def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)[:40]

def generate_application_draft(job: Dict[str, Any], profile: Dict[str, Any], match_analysis: Dict[str, Any]) -> Path:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{date_str}_{slugify(job['company'])}_{slugify(job['title'])}"
    job_folder = DRAFTS_DIR / folder_name
    job_folder.mkdir(parents=True, exist_ok=True)
    
    matching_skills_str = ", ".join(match_analysis.get("matching_skills", ["Ruby on Rails", "PostgreSQL", "AWS"]))
    lang = match_analysis.get("language", "en")
    
    # 1. info_vacante.md
    info_content = f"""# Resumen de Vacante: {job['title']} en {job['company']}

* **Empresa:** {job['company']}
* **Cargo:** {job['title']}
* **Ubicación:** {job.get('location', 'Berlin, Germany')}
* **Fecha de detección:** {date_str}
* **Score de Compatibilidad:** {match_analysis['match_score']}%
* **Idioma detectado:** {'Alemán' if lang == 'de' else 'Inglés'}
* **Habilidades coincidentes:** {matching_skills_str}
* **Enlace directo para postular:** [{job.get('url', 'Ver vacante')}]({job.get('url', '#')})

---

### Descripción del puesto
{job.get('description', 'Sin descripción provista.')}

---

### Siguientes pasos:
1. Revisa tu `CV_Personalizado.md` y `Cover_Letter.md` en esta carpeta.
2. Abre el enlace arriba y postúlate.
3. Mueve esta carpeta a `../enviadas/` una vez postulado, o a `../descartadas/` si decides no aplicar.
"""
    with open(job_folder / "info_vacante.md", "w", encoding="utf-8") as f:
        f.write(info_content)
        
    # 2. Cover_Letter.md
    templates_path = TEMPLATES_DIR / "cover_letter_templates.json"
    if templates_path.exists():
        with open(templates_path, "r", encoding="utf-8") as f:
            cl_templates = json.load(f)
        tpl = cl_templates.get(lang, cl_templates["en"])
    else:
        tpl = {
            "greeting": f"Dear Hiring Team at {job['company']},",
            "opening": f"I am writing to express my strong interest in the {job['title']} position.",
            "body_matching": f"With deep expertise in {matching_skills_str}, I am well prepared to contribute to your goals.",
            "berlin_status": "Based in Berlin with full work authorization.",
            "closing": "I look forward to discussing how I can add value to your team.",
            "signoff": "Best regards,\n\nJesús Cárdenas"
        }
        
    letter_text = f"""{tpl['greeting'].format(company=job['company'], role=job['title'])}

{tpl['opening'].format(company=job['company'], role=job['title'])}

{tpl['body_matching'].format(company=job['company'], role=job['title'], matching_skills=matching_skills_str)}

{tpl['berlin_status']}

{tpl['closing'].format(company=job['company'], role=job['title'])}

{tpl['signoff']}
"""
    with open(job_folder / f"Cover_Letter_{slugify(job['company'])}.md", "w", encoding="utf-8") as f:
        f.write(letter_text)

    # 3. CV_Personalizado.md (Strict Subset from master profile)
    master_cv_path = TEMPLATES_DIR / "cv_master.md"
    if master_cv_path.exists():
        with open(master_cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()
    else:
        cv_text = f"# Jesús Cárdenas A\nSenior Software Engineer\nTarget: {job['title']} at {job['company']}"
        
    cv_header = f"> **Target Application:** {job['title']} at {job['company']} (Match: {match_analysis['match_score']}%)  \n> **Key Highlights:** {matching_skills_str}\n\n"
    tailored_cv = cv_header + cv_text
    
    with open(job_folder / f"CV_{slugify(job['company'])}.md", "w", encoding="utf-8") as f:
        f.write(tailored_cv)
        
    return job_folder
