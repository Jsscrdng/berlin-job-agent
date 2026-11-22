#!/usr/bin/env python3
import os
import json
import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.matcher import load_master_profile, evaluate_match
from src.generator import generate_application_draft
from src.storage import init_db, is_job_processed, record_job
from src.notifier import send_telegram_notification

SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"

def load_settings():
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def run_job_intake(jobs_list, location="Berlin", role="Software Developer", primary_techs=None):
    if primary_techs is None:
        primary_techs = ["Ruby on Rails", "Ruby"]
        
    init_db()
    profile = load_master_profile()
    processed_count = 0
    generated_folders = []
    
    print("\n" + "="*70)
    print("🎯 BERLIN JOB APPLICATION AGENT (Programmable Search Mode)")
    print("="*70)
    print(f"📍 Ubicación objetivo: {location}")
    print(f"💼 Rol / Cargo:        {role}")
    print(f"🛠️  Tecnologías clave:  {', '.join(primary_techs)}")
    print("="*70)
    
    for job in jobs_list:
        title = job.get("title", role)
        company = job.get("company", "Company")
        url = job.get("url", "#")
        job_loc = job.get("location", location)
        description = job.get("description", "")
        
        # 1. Deduplication check
        if is_job_processed(company, title, url):
            print(f"⏩ [SKIP] Ya procesada: {company} - {title}")
            continue
            
        # 2. Matching evaluation using programmable variables
        analysis = evaluate_match(
            job_title=title, 
            job_description=description, 
            profile=profile,
            target_location=location,
            primary_techs=primary_techs
        )
        score = analysis["match_score"]
        
        print(f"\n🔍 Analizando: {company} | {title}")
        print(f"   Score: {score}% | Idioma: {analysis['language'].upper()} | Skills: {', '.join(analysis['matching_skills'])}")
        
        if analysis["is_qualified"]:
            folder = generate_application_draft(job, profile, analysis)
            record_job(company, title, url, job_loc, score, status="STAGED")
            generated_folders.append((company, title, score, folder, url))
            processed_count += 1
            print(f"   ✅ [BORRADOR CREADO] -> {folder.name}")
        else:
            print(f"   ⚠️ [DESCARTADO] No cumple umbral o ubicación ({score}%)")
            record_job(company, title, url, job_loc, score, status="DISCARDED")
            
    print("\n" + "-"*70)
    print(f"🏁 Proceso completado: {processed_count} nuevos borradores generados en 'vacantes_para_enviar/'.")
    if generated_folders:
        print("\n📁 Carpetas listas para tu revisión:")
        telegram_payload = []
        for comp, tit, sc, fld, u in generated_folders:
            print(f"  • [{sc}% Match] {comp} - {tit}: {fld.name}")
            telegram_payload.append({
                "company": comp,
                "title": tit,
                "score": sc,
                "folder": fld.name,
                "url": u
            })
        send_telegram_notification(telegram_payload)
    print("="*70 + "\n")

def main():
    settings = load_settings()
    search_cfg = settings.get("search", {})
    
    # Priority: CLI argument > Environment Variable > settings.json default
    default_location = os.getenv("JOB_SEARCH_LOCATION", search_cfg.get("location", "Berlin"))
    default_role = os.getenv("JOB_SEARCH_ROLE", search_cfg.get("role", "Software Developer"))
    default_tech_str = os.getenv("JOB_SEARCH_TECH", ", ".join(search_cfg.get("primary_technologies", ["Ruby on Rails", "Ruby"])))

    parser = argparse.ArgumentParser(description="Berlin Job Application Agent (Indeed)")
    parser.add_argument("--location", type=str, default=default_location, help="Ubicación de búsqueda (ej. Berlin, Hamburg)")
    parser.add_argument("--role", type=str, default=default_role, help="Rol o cargo (ej. Software Developer, Backend Engineer)")
    parser.add_argument("--tech", type=str, default=default_tech_str, help="Tecnologías clave separadas por comas (ej. 'Ruby on Rails, PostgreSQL')")
    parser.add_argument("--url", type=str, help="URL de vacante para ingesta manual")
    parser.add_argument("--company", type=str, default="Empresa en Berlín", help="Nombre de la empresa")
    parser.add_argument("--title", type=str, help="Título del puesto (opcional si se pasa --role)")
    parser.add_argument("--description", type=str, default="", help="Descripción del puesto")
    parser.add_argument("--sample", action="store_true", help="Ejecutar con vacantes de muestra")
    
    args = parser.parse_args()
    
    primary_techs = [t.strip() for t in args.tech.split(",") if t.strip()]
    job_title = args.title or args.role
    
    if args.url:
        jobs = [{
            "company": args.company,
            "title": job_title,
            "url": args.url,
            "location": args.location,
            "description": args.description or f"Position for {job_title} in {args.location}. Required tech: {', '.join(primary_techs)}."
        }]
    else:
        # Dynamic sample jobs based on search variables
        tech_headline = primary_techs[0] if primary_techs else "Backend"
        jobs = [
            {
                "company": "Trade Republic",
                "title": f"Senior {job_title} ({tech_headline})",
                "location": f"{args.location}, Germany",
                "url": "https://de.indeed.com/viewjob?jk=tr_berlin_rails_01",
                "description": f"We are seeking a {job_title} in {args.location}. Requirements: expertise in {', '.join(primary_techs)}, PostgreSQL query optimization, AWS cloud infrastructure, microservices, and TDD with RSpec."
            },
            {
                "company": "Zalando SE",
                "title": f"Fullstack {job_title} ({tech_headline} & React)",
                "location": f"{args.location} (Hybrid)",
                "url": "https://de.indeed.com/viewjob?jk=zalando_berlin_fullstack_02",
                "description": f"Zalando is looking for a {job_title} in {args.location}. Key skills: {', '.join(primary_techs)}, React, PostgreSQL, Docker, CI/CD, A/B testing experience, and team collaboration."
            },
            {
                "company": "Delivery Hero",
                "title": f"Senior {job_title} - Payments & Core Services",
                "location": f"{args.location}, Germany",
                "url": "https://de.indeed.com/viewjob?jk=dh_berlin_backend_03",
                "description": f"Join our core engineering team in {args.location}. Responsibilities: {', '.join(primary_techs)}, SQL data consistency across distributed systems, AWS and Redis."
            }
        ]
        
    run_job_intake(jobs, location=args.location, role=job_title, primary_techs=primary_techs)

if __name__ == "__main__":
    main()
