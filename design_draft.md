# Berlin Job Application Agent (Indeed.de)

*   **Author:** Jesús Cárdenas & Antigravity (Elephant Orchestrator)
*   **Status:** Implemented & Verified (Post EGM Goldfish Audit)
*   **Date:** 2026-11-22

--------------------------------------------------------------------------------

## Overview

Automated background system that identifies target tech job postings in Berlin, Germany (`de.indeed.com`), evaluates compatibility against Jesús Cárdenas's consolidated **Master Profile**, and compiles tailored application packets (`info_vacante.md`, `CV_{Company}.md`, and `Cover_Letter_{Company}.md`). 

All generated materials are staged in `vacantes_para_enviar/` for human review prior to submission.

---

## Architectural Resolutions (Addressing EGM Goldfish Audits)

1. **Anti-Scraping & Ingestion Model:**
   * Hybrid ingestion: Automated CLI querying combined with manual fast-ingest (`python run_pipeline.py --url <link>`).
   * No CAPTCHA bypass attempted; avoids fragile DOM selectors by using structured job schemas.
2. **Strict Zero-Hallucination Policy:**
   * The CV generator operates on a strict subset rule: bullets and achievements are selected and reordered strictly from `mi_perfil/perfil_maestro.json`, preventing AI hallucination of credentials or dates.
3. **State Persistence & Deduplication:**
   * SQLite engine (`jobs_tracker.db`) indexes job hashes (`sha256(company|title|url)`). Repeated pipeline executions automatically skip previously processed or applied jobs.
4. **Bilingual Berlin Job Support:**
   * Language auto-detection (German vs. English). English listings generate international standard materials; German listings generate formal German materials (*Sehr geehrtes Hiring-Team*, *Siezen*).
   * Incorporates critical German employment attributes: Berlin residence, German phone, ANABIN H+ certified degree (*Bachelor Elektrotechnik*), and unrestricted work authorization.

---

## Candidate Master Profile Summary

* **Name:** Jesús Cárdenas A
* **Title:** Senior Software Engineer / Fullstack & Backend Engineer (8+ years experience)
* **Core Stack:** Ruby on Rails, PostgreSQL, AWS, React, Python, Docker, TDD (RSpec/Capybara)
* **Recent Experience:** 
  * *Sofatutor GmbH (Berlin, Feb 2022 – Dec 2025):* Backend/Fullstack, 1M+ students, Stripe integrations, A/B testing, mentorship.
  * *Ideaware Co S.A.S (Aug 2019 – Jan 2022):* Backend Tech Lead, Bucket.io 2.0, SQL optimization on >1M records (>50% speedup).
  * *Gases del Caribe (Dec 2018 – Jul 2019):* Rails microcredit platform MVP, real-time sync with Oracle PL/SQL.
  * *Nativapps & Emotiva:* DevOps, mobile apps, IoT telemetry.
* **Education:** Universidad del Norte (ANABIN H+ Equivalence, Orgullo Caribe Full Scholarship).
