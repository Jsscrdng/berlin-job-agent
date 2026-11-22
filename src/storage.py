import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "jobs_tracker.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_hash TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        url TEXT NOT NULL,
        match_score REAL,
        status TEXT DEFAULT 'DISCOVERED', -- DISCOVERED, STAGED, APPLIED, DISCARDED
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def compute_hash(company: str, title: str, url: str) -> str:
    norm = f"{company.strip().lower()}|{title.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()

def is_job_processed(company: str, title: str, url: str) -> bool:
    init_db()
    h = compute_hash(company, title, url)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM jobs WHERE job_hash = ?", (h,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def record_job(company: str, title: str, url: str, location: str, match_score: float, status: str = "STAGED"):
    init_db()
    h = compute_hash(company, title, url)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO jobs (job_hash, title, company, location, url, match_score, status, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (h, title, company, location, url, match_score, status, datetime.now()))
    conn.commit()
    conn.close()

def update_status(job_hash: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE job_hash = ?", (status, datetime.now(), job_hash))
    conn.commit()
    conn.close()
