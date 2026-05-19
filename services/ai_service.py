"""
services/ai_service.py — Integrazione con Claude (Anthropic).
Gestisce la comprensione del linguaggio naturale e le analisi.
"""
import json
import anthropic
from datetime import datetime
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-5"

# ── SYSTEM PROMPT PRINCIPALE ──────────────────────────────────────────────────
def _build_system_prompt() -> str:
    now = datetime.now().strftime("%A %d %B %Y, ore %H:%M")
    return f"""Sei un assistente personale intelligente, mental coach e diario della salute.
Sei integrato in un bot Telegram e parli SEMPRE in italiano.

Data e ora attuale: {now}

Il tuo compito è:
1. Capire l'intenzione dell'utente dal linguaggio naturale
2. Classificare il tipo di richiesta
3. Restituire un JSON strutturato

Rispondi SEMPRE e SOLO con un JSON valido (nessun testo fuori dal JSON):

{{
  "intent": "agenda_add | agenda_query | agenda_edit | food | spesa | checkin_response | general",
  "response_text": "risposta in linguaggio naturale per l'utente (cordiale e motivante)",
  "data": {{ ... dati strutturati in base all'intent ... }}
}}

── Intent: agenda_add ──
data = {{
  "title": "titolo evento",
  "start": "YYYY-MM-DDTHH:MM",
  "end": "YYYY-MM-DDTHH:MM",
  "category": "lavoro | sport | salute | personale | sport_milan",
  "description": "note aggiuntive"
}}

── Intent: agenda_query ──
data = {{
  "timeframe": "today | tomorrow | week | specific_date",
  "specific_date": "YYYY-MM-DD (solo se timeframe=specific_date)"
}}

── Intent: food ──
data = {{
  "meal_type": "colazione | pranzo | cena | spuntino",
  "foods": ["alimento1", "alimento2", ...],
  "quality_score": 1-10,
  "calories_est": numero stimato,
  "notes": "osservazioni nutrizionali brevi"
}}
── Intent: spesa ──
data ha questi campi: amount (numero), category (cibo, trasporti, shopping, svago, dipendenze, beni_primari, lavoro, altro), description (testo breve)

── Intent: checkin_response ──
data = {{
  "sentiment": "positivo | neutro | negativo",
  "completed": ["evento1", ...],
  "missed": ["evento2", ...],
  "reasons": {{"evento2": "motivazione"}}
}}

── Intent: general ──
data = {{}}
"""


# ── FUNZIONE PRINCIPALE ───────────────────────────────────────────────────────
def process_message(user_text: str) -> dict:
    """
    Invia il messaggio a Claude e restituisce un dict strutturato.
    Gestisce anche gli errori di parsing JSON.
    """
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=_build_system_prompt(),
            messages=[{"role": "user", "content": user_text}]
        )
        raw = response.content[0].text.strip()

        # Pulizia backtick Markdown se presenti
        raw = raw.replace("```json", "").replace("```", "").strip()

        return json.loads(raw)

    except json.JSONDecodeError:
        return {
            "intent": "general",
            "response_text": "Ho capito il messaggio, ma ho avuto un problema tecnico. Riprova!",
            "data": {}
        }
    except Exception as e:
        return {
            "intent": "general",
            "response_text": f"Errore di connessione all'AI: {str(e)}",
            "data": {}
        }


# ── ANALISI SETTIMANALE ───────────────────────────────────────────────────────
def generate_weekly_analysis(checkins: list, food_entries: list, events: list) -> dict:
    """Genera il report settimanale analizzando tutti i dati della settimana."""
    prompt = f"""Analizza questi dati della settimana dell'utente e genera un report completo.

CHECK-IN SERALI:
{json.dumps(checkins, indent=2, ensure_ascii=False)}

DIARIO ALIMENTARE:
{json.dumps(food_entries, indent=2, ensure_ascii=False)}

EVENTI/AGENDA:
{json.dumps(events, indent=2, ensure_ascii=False)}

Rispondi SOLO con un JSON:
{{
  "report_text": "report narrativo completo in italiano, empatico e motivante",
  "strengths": ["punto di forza 1", ...],
  "improvements": ["area di miglioramento 1", ...],
  "patterns": ["pattern identificato 1 (es: ogni martedì salti la palestra)", ...],
  "suggestions": ["suggerimento concreto 1", ...],
  "food_summary": {{
    "overall_quality": 1-10,
    "main_issues": ["problema 1", ...],
    "good_habits": ["abitudine positiva 1", ...],
    "weekly_tip": "consiglio alimentare della settimana"
  }}
}}"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}
