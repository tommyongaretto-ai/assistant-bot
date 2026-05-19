"""
database/models.py — Operazioni CRUD per tutte le tabelle.
"""
import json
from datetime import datetime
from database.db import get_connection


# ── EVENTI ────────────────────────────────────────────────────────────────────

def add_event(title: str, start: str, end: str,
              category: str = "personale", source: str = "utente",
              description: str = "") -> int:
    """Aggiunge un evento e restituisce l'ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO events (title, description, start_datetime, end_datetime, category, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, start, end, category, source))
    conn.commit()
    event_id = c.lastrowid
    conn.close()
    return event_id


def get_events_for_date(date_str: str) -> list:
    """Restituisce tutti gli eventi per una data (formato YYYY-MM-DD)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
        WHERE start_datetime LIKE ?
        ORDER BY start_datetime
    """, (f"{date_str}%",))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_events_for_week(week_start: str, week_end: str) -> list:
    """Restituisce gli eventi tra due date."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
        WHERE start_datetime BETWEEN ? AND ?
        ORDER BY start_datetime
    """, (week_start, week_end + "T23:59"))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def check_conflicts(start: str, end: str) -> list:
    """Trova eventi sovrapposti a un nuovo slot."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM events
        WHERE start_datetime < ? AND end_datetime > ?
    """, (end, start))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def delete_event(event_id: int) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()
    return deleted


# ── DIARIO ALIMENTARE ─────────────────────────────────────────────────────────

def add_food_entry(meal_type: str, raw_description: str,
                   ai_analysis: dict = None, quality_score: int = 5,
                   calories_est: int = 0) -> int:
    conn = get_connection()
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
        INSERT INTO food_diary (date, meal_type, raw_description, ai_analysis, quality_score, calories_est)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (today, meal_type, raw_description,
          json.dumps(ai_analysis or {}), quality_score, calories_est))
    conn.commit()
    entry_id = c.lastrowid
    conn.close()
    return entry_id


def get_food_for_week(week_start: str, week_end: str) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM food_diary
        WHERE date BETWEEN ? AND ?
        ORDER BY date, created_at
    """, (week_start, week_end))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ── CHECK-IN SERALI ───────────────────────────────────────────────────────────

def save_checkin(date: str, bot_message: str, user_response: str,
                 missed: list = None, reasons: dict = None,
                 sentiment: str = "neutro"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO daily_checkins
        (date, bot_message, user_response, sentiment, missed_events, miss_reasons)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, bot_message, user_response, sentiment,
          json.dumps(missed or []), json.dumps(reasons or {})))
    conn.commit()
    conn.close()


def get_checkins_for_week(week_start: str, week_end: str) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM daily_checkins
        WHERE date BETWEEN ? AND ?
        ORDER BY date
    """, (week_start, week_end))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ── REPORT SETTIMANALI ────────────────────────────────────────────────────────

def save_weekly_report(week_start: str, week_end: str, report_text: str,
                       strengths: list, improvements: list,
                       patterns: list, suggestions: list, food_summary: dict):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO weekly_reports
        (week_start, week_end, report_text, strengths, improvements,
         patterns_identified, suggestions, food_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (week_start, week_end, report_text,
          json.dumps(strengths), json.dumps(improvements),
          json.dumps(patterns), json.dumps(suggestions),
          json.dumps(food_summary)))
    conn.commit()
    conn.close()
