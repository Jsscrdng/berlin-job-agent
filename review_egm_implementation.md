# Implementation Readiness Audit Report: Berlin Job Application Agent

**Auditor:** Implementation Readiness Goldfish (Pragmatic Tech Lead & Senior Implementing Engineer)  
**Target Document:** [`design_draft.md`](file:///Users/jesuscardenas/.gemini/antigravity/scratch/berlin_job_agent/design_draft.md)  
**Status:** **NOT READY FOR IMPLEMENTATION (Design Gaps & Blockers Identified)**

---

## 1. Executive Summary

El documento define una visión de producto clara y CUJs bien orientados a human-in-the-loop. Sin embargo, **un desarrollador no puede comenzar a escribir código hoy** sin tomar decisiones arquitectónicas críticas que no han sido documentadas:
1. **Definición de librerías y contratos de red:** No hay decisión sobre cómo interactuar con `de.indeed.com` (Cloudflare Turnstile bloquea HTTP requests directos).
2. **Esquema de datos:** `perfil_maestro.json` y la estructura intermedia de la vacante (`JobPosting`) no tienen campos, tipos ni reglas de validación.
3. **Mecanismo de deduplicación y persistencia:** No existe un registro para evitar evaluar y re-generar vacantes duplicadas en ejecuciones subsiguientes.
4. **Algoritmo de scoring:** No se especifica cómo se calcula el threshold del 75% (¿embeddings, matching léxico TF-IDF o llamada LLM?).
5. **Pipeline de formato final:** Los ATS de reclutamiento no aceptan Markdown; falta el pipeline de renderizado a PDF ATS-compliant.

---

## 2. Detailed Audit Findings

### Finding 1 [BLOCKER]: Estrategia de Scraping de Indeed y Bypass de Anti-Bot sin Definir
* `de.indeed.com` cuenta con protecciones Cloudflare Turnstile, browser fingerprinting y rate-limiting agresivo. `requests` o `httpx` estándar fallan con HTTP 403.
* **Decisión requerida:**
  1. Usar un agregador optimizado (`python-jobspy` con soporte para Indeed sin navegador pesado).
  2. Fallback de navegador headless controlado o ingesta asistida manual vía URL (`python run_pipeline.py --url <link>`).

### Finding 2 [BLOCKER]: Ausencia de Schema para `perfil_maestro.json` y Normalización de Vacante
* Para el mercado laboral alemán (Berlín), se requieren campos específicos: permiso de trabajo en Alemania/UE, nivel CEFR de Alemán e Inglés, período de preaviso (*Kündigungsfrist*), pretensión salarial (*Gehaltsvorstellung*).

### Finding 3 [BLOCKER]: Falta de Especificación del Algoritmo de Matching (Threshold 75%)
* Filtro en 2 fases:
  1. **Heurística dura (Fase 1):** Requisitos indispensables (idioma, permiso laboral, ubicación Berlín).
  2. **Scoring semántico (Fase 2):** Match de skills y responsabilidades con justificación estructurada.

### Finding 4 [MAJOR]: Deduplicación y Persistencia de Estado
* Necesidad de base de datos ligera SQLite (`jobs_tracker.db`) indexada por `job_id` y hash de contenido para evitar duplicados en ejecuciones repetidas.

### Finding 5 [MAJOR]: Ausencia de Pipeline de Generación de PDF (ATS Friendly)
* Los ATS exigen PDF. Incorporar renderizado determinista a PDF ATS limpio (vía HTML/CSS minimalista con Jinja2 y `weasyprint`).

### Finding 6 [MAJOR]: Contrato de Prompting y Prevención de Alucinaciones
* **Regla estricta:** El LLM no puede inventar experiencia; solo puede reordenar y seleccionar bullets validados del perfil maestro.
* **Bilingüe:** Si la vacante es en alemán, redactar *Anschreiben* formal en alemán (*Siezen*); si es en inglés, en inglés formal.

---

## 3. Schema Propuesto: `perfil_maestro.json`

Estructura Pydantic adaptada a estándares de empleo en Berlín:
- `personal_info`: Datos de contacto y enlaces.
- `work_authorization`: `has_german_work_permit`, `visa_type`, `notice_period_months`.
- `languages`: Idioma y nivel CEFR (A1-C2, Native).
- `skills`: `hard_skills`, `tools_and_frameworks`, `soft_skills`.
- `experiences`: Historial de cargos con `highlights` atómicos etiquetados con skills asociadas.
- `education`: Títulos, instituciones y años.
