# INFORME DE REVISIÓN ARQUITECTÓNICA (EGM HOSTILE DESIGN CRITIC)

**Documento Auditado:** `/Users/jesuscardenas/.gemini/antigravity/scratch/berlin_job_agent/design_draft.md`  
**Auditor:** Design Critic Goldfish (Senior Systems & Security Critic)  
**Veredicto General:** **RECHAZADO (REQUIERE REVISIÓN ARQUITECTÓNICA PROFUNDA)**

---

## 1. Resumen Ejecutivo

El borrador describe un concepto atractivo pero **arquitectónicamente ingenuo y frágil**. Trata el mayor punto de fallo del sistema (la evasión de anti-bot y Cloudflare en `de.indeed.com`) como una simple "Open Question" en lugar de un requerimiento fundacional. Además, carece de controles contra alucinaciones en CVs (riesgo legal/profesional de falseo curricular), carece de una estrategia de deduplicación persistente (confía en mover carpetas locales) y produce archivos Markdown (`.md`) que los ATS de las empresas no aceptan.

---

## 2. Hallazgos Críticos y Vulnerabilidades

### 🚨 HALLAZGO 1 [BLOCKER]: Dependencia No Resuelta de Scraping en Indeed y Barreras Anti-Bot
* **Gravedad:** `Blocker`
* **Alcance Afectado:** `design_draft.md`, Líneas 33, 47, 54. Subflujo de Ingesta (`run_pipeline.py`).
* **Falla Técnica:** 
  `de.indeed.com` cuenta con una de las infraestructuras anti-scraping más agresivas del mercado (Cloudflare Turnstile, detección JA3/JA4 TLS fingerprinting, rate-limiting por IP y DOM obfuscation dinámico). Asumir que un script estándar en cron/schedule (`run_pipeline.py`) a las 09:00 y 17:00 puede simplemente "hacer query a Indeed" provocará baneos de IP en las primeras 24 horas o bloqueos inmediatos por CAPTCHA. Los feeds RSS públicos de Indeed fueron retirados/restringidos hace años y la API oficial exige acuerdos de partnership comercial.
* **Recomendación:**
  1. Definir explícitamente el stack de extracción: ¿Uso de Playwright con `playwright-stealth` y rotación de proxies residenciales? ¿O uso de scrapers de terceros especializados (BrightData, ScraperAPI, Apify Indeed Scraper Actor)?
  2. Implementar un fallback desacoplado: Diseñar una ingesta manual alternativa (ej. extensión de navegador ligera donde el usuario navega normalmente y "empuja" la vacante con 1 clic al pipeline, o ingesta vía clipboard/URL) para que el agente no quede paralizado cuando Indeed modifique sus defensas.

---

### 🚨 HALLAZGO 2 [BLOCKER]: Riesgo de Alucinación y Modificación Inexacta de Experiencia Laboral
* **Gravedad:** `Blocker`
* **Alcance Afectado:** `design_draft.md`, Líneas 38-39 (`CV_Personalizado.md`).
* **Falla Técnica:**
  El documento afirma: *"Re-ordered bullet points emphasizing exact matching keywords"*. En pipelines LLM sin constraints deterministas rígidos, los modelos de lenguaje tienden a fabricar métricas, herramientas secundarias o fechas para maximizar el match score ATS ("semantic drift"). Si un usuario en una "revisión de 5 minutos" envía un CV con claims falsos generados por el LLM, las repercusiones profesionales y legales son críticas.
* **Recomendación:**
  1. **Strict Subset Constraint:** Establecer como principio de diseño que el CV generado NUNCA inventa texto; únicamente puede *filtrar*, *reordenar* o *seleccionar* bullets preexistentes y validados dentro de `perfil_maestro.json`.
  2. Implementar una capa de aserción algorítmica (diff audit): Un script determinista (sin LLM) que compare el CV generado contra el `perfil_maestro.json` y aborte si detecta entidades, tecnologías o empresas que no figuren en la base canónica.

---

### ⚠️ HALLAZGO 3 [MAJOR]: Inutilidad Práctica del Formato Markdown (`.md`) ante ATS
* **Gravedad:** `Major`
* **Alcance Afectado:** `design_draft.md`, Líneas 38-39, 56.
* **Falla Técnica:**
  Ningún sistema ATS corporativo (Workday, Greenhouse, Lever, BambooHR, Indeed Easy Apply) acepta archivos `.md`. Obligar al usuario a copiar y pegar Markdown a Word/Google Docs y darle formato cada mañana destruye la promesa de "5-minute review" (CUJ 2). Además, los ATS requieren capas de texto estructuradas y tipografía estándar en PDF para parsear adecuadamente.
* **Recomendación:**
  El pipeline debe incluir un paso de compilación determinista headless a PDF estándar ATS (utilizando herramientas como Typst, Weasyprint o LaTeX con plantillas de una sola columna sin tablas complejas) listo para adjuntar directamente en la postulación.

---

### ⚠️ HALLAZGO 4 [MAJOR]: Deduplicación y Gestión de Estado Basada en File-System Frágil
* **Gravedad:** `Major`
* **Alcance Afectado:** `design_draft.md`, Líneas 40, 60-70 (CUJ 1 & 2).
* **Falla Técnica:**
  El diseño utiliza el movimiento de carpetas (`vacantes_para_enviar/` -> `enviadas/` o `descartadas/`) como su única base de datos de estado.
  1. Las empresas republicitan la misma oferta cada 7 días con distintos IDs de publicación (`jk` en Indeed). Sin una base de datos local (SQLite o JSON indexado) con hashing de contenido (`sha256(company + title + normalized_description)`), el scraper volverá a generar drafts duplicados de vacantes ya descartadas o enviadas.
  2. Si el usuario renombra o borra una carpeta manualmente, el crawler pierde la trazabilidad de qué vacantes ya fueron vistas.
* **Recomendación:**
  Incorporar una base de datos de estado ligera (SQLite embebido o `history.db` con tablas `seen_jobs`, `applications`, `blacklisted_companies`) con índices por `job_key` y hash semántico de texto.

---

### ⚠️ HALLAZGO 5 [MAJOR]: Falta de Presupuesto de Tokens, Modelo Económico y Privacidad de Datos (PII)
* **Gravedad:** `Major`
* **Alcance Afectado:** `design_draft.md`, Líneas 9-16, 34-39.
* **Falla Técnica:**
  1. **Coste/Tokens:** Una descripción de puesto en Indeed suele tener 800-1500 palabras; un Master Profile consolidado puede tener 3000 palabras. Ejecutar scoring y generación para decenas de vacantes diarias sin filtrado heurístico previo multiplicará el consumo de tokens y la latencia.
  2. **Privacidad (GDPR/PII):** El Master Profile contiene datos altamente sensibles (dirección física en Berlín, teléfono, historial salarial, nombres de empleadores). El diseño no estipula qué proveedores LLM se usarán ni si se sanitizan los datos antes del envío a APIs externas.
* **Recomendación:**
  1. Diseñar un filtrado en cascada en 2 etapas: 
     - *Etapa 1 (Gratis/Local):* Filtros regex/keyword matching locales (skills indispensables, ubicación Berlín, exclusión de juniors/seniors según aplique).
     - *Etapa 2 (LLM):* Scoring y generación sólo para el top 10% que supere la Etapa 1.
  2. Definir si se usarán modelos locales (Ollama/Llama 3) para mantener el PII en la máquina del usuario o si se implementará anonimización de datos personales previa al prompt.

---

### 💡 HALLAZGO 6 [NIT]: Ambigüedad en la Detección y Redacción Lingüística (DE vs. EN)
* **Gravedad:** `Nit`
* **Alcance Afectado:** `design_draft.md`, Líneas 39, 55.
* **Falla Técnica:**
  En el mercado de Berlín conviven ofertas en inglés (tech/startups) y en alemán (corporativo/público). Generar un *Anschreiben* en alemán a partir de un perfil maestro escrito en inglés mediante traducción libre suele resultar en un tono forzado o vocabulario técnico descontextualizado.
* **Recomendación:**
  `perfil_maestro.json` debe contar con secciones bilingües nativas (bloque en alemán y bloque en inglés auditados previamente por el usuario) en lugar de depender de traducciones en tiempo de ejecución.

---

## 3. Conclusión y Siguientes Pasos
El documento actual se encuentra en nivel de **Wishlist**, no de **Diseño Técnico Ejecutable**. Para que el Elephant Orchestrator pueda avanzar a la fase de implementación, es mandatorio resolver:
1. Mecanismo real de ingesta (evasión de Cloudflare o método asistido por navegador).
2. Modelo relacional/almacén de estado (SQLite) para deduplicación.
3. Compilación a PDF ATS-friendly.
4. Regla estricta de "cero alucinaciones" en la adaptación curricular.
