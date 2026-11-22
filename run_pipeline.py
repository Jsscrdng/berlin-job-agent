#!/usr/bin/env python3
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

def run_job_intake(jobs_list):
    init_db()
    profile = load_master_profile()
    processed_count = 0
    generated_folders = []
    
    print("\n" + "="*70)
    print("🎯 BERLIN JOB APPLICATION AGENT (EGM Orchestrator)")
    print("="*70)
    
    for job in jobs_list:
        title = job.get("title", "Software Engineer")
        company = job.get("company", "Company")
        url = job.get("url", "#")
        location = job.get("location", "Berlin, Germany")
        description = job.get("description", "")
        
        # 1. Deduplication check
        if is_job_processed(company, title, url):
            print(f"⏩ [SKIP] Ya procesada: {company} - {title}")
            continue
            
        # 2. Matching evaluation
        analysis = evaluate_match(title, description, profile)
        score = analysis["match_score"]
        
        print(f"\n🔍 Analizando: {company} | {title}")
        print(f"   Score: {score}% | Idioma: {analysis['language'].upper()} | Skills: {', '.join(analysis['matching_skills'])}")
        
        if analysis["is_qualified"]:
            folder = generate_application_draft(job, profile, analysis)
            record_job(company, title, url, location, score, status="STAGED")
            generated_folders.append((company, title, score, folder, url))
            processed_count += 1
            print(f"   ✅ [BORRADOR CREADO] -> {folder.name}")
        else:
            print(f"   ⚠️ [DESCARTADO] Score por debajo del umbral mínimo ({score}%)")
            record_job(company, title, url, location, score, status="DISCARDED")
            
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
    parser = argparse.ArgumentParser(description="Berlin Job Application Agent")
    parser.add_argument("--url", type=str, help="URL de vacante para ingesta manual")
    parser.add_argument("--company", type=str, default="Empresa en Berlín", help="Nombre de la empresa")
    parser.add_argument("--title", type=str, default="Senior Backend Developer", help="Título del puesto")
    parser.add_argument("--description", type=str, default="", help="Descripción del puesto")
    parser.add_argument("--sample", action="store_true", help="Ejecutar con vacantes de muestra de Indeed Berlín")
    
    args = parser.parse_args()
    
    if args.url:
        jobs = [{
            "company": args.company,
            "title": args.title,
            "url": args.url,
            "location": "Berlin, Germany",
            "description": args.description or f"Senior Backend Engineer required. Strong expertise in Ruby on Rails, PostgreSQL, AWS, and RESTful APIs in an Agile environment."
        }]
    else:
        # Sample realistic Berlin vacancies (Tech startups & Scaleups in Berlin)
        jobs = [
            {
                "company": "Trade Republic",
                "title": "Senior Backend Engineer (Ruby on Rails / PostgreSQL)",
                "location": "Berlin, Germany",
                "url": "https://de.indeed.com/viewjob?jk=tr_berlin_rails_01",
                "description": "We are seeking a Senior Backend Engineer in Berlin. Requirements: 5+ years with Ruby on Rails, deep experience with PostgreSQL query optimization, AWS cloud infrastructure, microservices, and TDD with RSpec. German or English fluency."
            },
            {
                "company": "Zalando SE",
                "title": "Fullstack Software Developer (Rails & React)",
                "location": "Berlin (Hybrid)",
                "url": "https://de.indeed.com/viewjob?jk=zalando_berlin_fullstack_02",
                "description": "Zalando is looking for a Fullstack Developer. Key skills: Ruby on Rails, React, PostgreSQL, Docker, CI/CD, A/B testing experience, and mentoring other developers. English language proficiency."
            },
            {
                "company": "Delivery Hero",
                "title": "Senior Backend Developer - Payments Integration",
                "location": "Berlin, Germany",
                "url": "https://de.indeed.com/viewjob?jk=dh_berlin_backend_03",
                "description": "Join our global payments team in Berlin. Responsibilities: Stripe and third-party financial API integrations, Ruby / Python backend services, SQL data consistency across distributed systems, AWS and Redis."
            }
        ]
        
    run_job_intake(jobs)

if __name__ == "__main__":
    main()
