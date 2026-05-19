"""
database/db.py — Connessione SQLite e schema del database.
Contiene tutte le tabelle dell'assistente personale.
"""
import sqlite3
import os
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Restituisce una connessione al database con row_factory abilitata."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # accesso colonne per nome
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Crea tutte le tabelle se non esistono già."""
    conn = get_connection()
    c = conn.cursor()

    # ── 1. EVENTI / AGENDA ────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT    NOT NULL,
            description     TEXT    DEFAULT '',
            start_datetime  TEXT    NOT NULL,          -- ISO: 2025-06-01T09:00
            end_datetime    TEXT    NOT NULL,
            category        TEXT    DEFAULT 'personale',
            source          TEXT    DEFAULT 'utente',  -- 'utente' | 'sport'
            is_confirmed    INTEGER DEFAULT 1,          -- 0 = proposta
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── 2. CHECK-IN SERALI ────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkins (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            date             TEXT    NOT NULL UNIQUE,   -- YYYY-MM-DD
            bot_message      TEXT,
            user_response    TEXT,
            sentiment        TEXT,                      -- positivo | neutro | negativo
            completed_events TEXT    DEFAULT '[]',      -- JSON lista titoli
            missed_events    TEXT    DEFAULT '[]',      -- JSON lista titoli
            miss_reasons     TEXT    DEFAULT '{}',      -- JSON {titolo: motivazione}
            created_at       TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── 3. DIARIO ALIMENTARE ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS food_diary (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            date             TEXT    NOT NULL,          -- YYYY-MM-DD
            meal_type        TEXT,                      -- colazione|pranzo|cena|spuntino
            raw_description  TEXT    NOT NULL,          -- testo libero dell'utente
            ai_analysis      TEXT    DEFAULT '{}',      -- JSON: cibi, macro, qualità
            calories_est     INTEGER DEFAULT 0,
            quality_score    INTEGER DEFAULT 5,         -- 1-10
            created_at       TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── 4. REPORT SETTIMANALI ─────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS weekly_reports (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start           TEXT    NOT NULL,      -- YYYY-MM-DD (lunedì)
            week_end             TEXT    NOT NULL,      -- YYYY-MM-DD (domenica)
            report_text          TEXT,
            strengths            TEXT    DEFAULT '[]',  -- JSON lista punti di forza
            improvements         TEXT    DEFAULT '[]',  -- JSON aree di miglioramento
            patterns_identified  TEXT    DEFAULT '[]',  -- JSON pattern trovati
            suggestions          TEXT    DEFAULT '[]',  -- JSON suggerimenti
            food_summary         TEXT    DEFAULT '{}',  -- JSON riepilogo alimentare
            created_at           TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── 5. PATTERN IDENTIFICATI ───────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS patterns (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT    NOT NULL,   -- 'abitudine_mancata'|'forza'|'suggerimento'
            description  TEXT    NOT NULL,
            frequency    INTEGER DEFAULT 1,
            first_seen   TEXT    DEFAULT (date('now')),
            last_seen    TEXT    DEFAULT (date('now')),
            is_active    INTEGER DEFAULT 1
        )
    """)
    # ── 6. TRACKER SPESE ─────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    DEFAULT 'generale',
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database inizializzato correttamente →", DB_PATH)
