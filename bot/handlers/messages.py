"""
bot/handlers/messages.py — Handler per messaggi in linguaggio naturale.
Processa i testi con AI e salva i dati nel DB.
"""
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

from services.ai_service import process_message
from database import models

logger = logging.getLogger(__name__)

# Stato conversazione semplice (in memoria)
# Nella Fase 2 useremo ConversationHandler di python-telegram-bot
_awaiting_checkin: dict[int, dict] = {}


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    logger.info(f"📩 Messaggio da {user_id}: {user_text[:80]}")

    # ── Controlla se aspettiamo una risposta al check-in ──────────────────────
    if user_id in _awaiting_checkin:
        await _handle_checkin_response(update, user_text, user_id)
        return

    # ── Processa con AI ───────────────────────────────────────────────────────
    result = process_message(user_text)
    intent = result.get("intent", "general")
    response_text = result.get("response_text", "Non ho capito, puoi ripetere?")
    data = result.get("data", {})

    logger.info(f"🧠 Intent: {intent}")

    # ── Routing in base all'intent ────────────────────────────────────────────
    if intent == "agenda_add":
        await _handle_agenda_add(update, data, response_text)

    elif intent == "agenda_query":
        await _handle_agenda_query(update, data, response_text)

    elif intent == "food":
        await _handle_food(update, data, response_text, user_text)

    elif intent == "checkin_response":
        await _handle_checkin_response(update, user_text, user_id, data)

    else:
        await update.message.reply_text(response_text)


# ── GESTIONE AGENDA ───────────────────────────────────────────────────────────

async def _handle_agenda_add(update, data, response_text):
    title = data.get("title")
    start = data.get("start")
    end = data.get("end")

    if not all([title, start, end]):
        await update.message.reply_text(
            "⚠️ Non sono riuscito a capire data e ora dell'impegno. "
            "Puoi essere più preciso? Es: 'Domani alle 10 riunione, finisce alle 11:30'"
        )
        return

    # Controlla conflitti
    conflitti = models.check_conflicts(start, end)

    # Salva evento
    event_id = models.add_event(
        title=title,
        start=start,
        end=end,
        category=data.get("category", "personale"),
        description=data.get("description", "")
    )

    if conflitti:
        nomi = ", ".join([c["title"] for c in conflitti])
        await update.message.reply_text(
            f"✅ *{title}* aggiunto!\n\n"
            f"⚠️ Attenzione: c'è un conflitto con: *{nomi}*\n"
            "Vuoi spostare o annullare l'impegno in conflitto?",
            parse_mode="Markdown"
        )
    else:
        ora_inizio = start[11:16] if len(start) > 10 else ""
        await update.message.reply_text(
            f"✅ {response_text}\n📌 *{title}* alle {ora_inizio} salvato!",
            parse_mode="Markdown"
        )


async def _handle_agenda_query(update, data, response_text):
    timeframe = data.get("timeframe", "today")
    today = datetime.now().strftime("%Y-%m-%d")

    if timeframe == "today":
        events = models.get_events_for_date(today)
        _mostra_eventi(update, events, f"Oggi {datetime.now().strftime('%d/%m')}")
    elif timeframe == "tomorrow":
        from datetime import timedelta
        domani = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        events = models.get_events_for_date(domani)
        await _mostra_lista(update, events, "Domani")
    else:
        await update.message.reply_text(response_text)


async def _mostra_lista(update, events, label):
    if not events:
        await update.message.reply_text(f"📅 Nessun impegno per {label}.")
        return
    righe = [f"📅 *{label}:*"]
    for e in events:
        ora = e["start_datetime"][11:16]
        righe.append(f"• {ora} — {e['title']}")
    await update.message.reply_text("\n".join(righe), parse_mode="Markdown")


# ── GESTIONE CIBO ─────────────────────────────────────────────────────────────

async def _handle_food(update, data, response_text, raw_text):
    models.add_food_entry(
        meal_type=data.get("meal_type", "pasto"),
        raw_description=raw_text,
        ai_analysis=data,
        quality_score=data.get("quality_score", 5),
        calories_est=data.get("calories_est", 0)
    )
    qualita = data.get("quality_score", 5)
    emoji = "🥗" if qualita >= 7 else "⚠️" if qualita <= 4 else "🍽️"
    await update.message.reply_text(
        f"{emoji} {response_text}\n\n"
        f"_Qualità pasto stimata: {qualita}/10_",
        parse_mode="Markdown"
    )


# ── GESTIONE CHECK-IN ─────────────────────────────────────────────────────────

def set_awaiting_checkin(user_id: int, bot_message: str):
    """Chiamato dallo scheduler quando invia il check-in serale."""
    _awaiting_checkin[user_id] = {
        "bot_message": bot_message,
        "timestamp": datetime.now().isoformat()
    }


async def _handle_checkin_response(update, user_text, user_id, data=None):
    ctx = _awaiting_checkin.pop(user_id, {})
    bot_message = ctx.get("bot_message", "")
    today = datetime.now().strftime("%Y-%m-%d")

    if data is None:
        result = process_message(user_text)
        data = result.get("data", {})

    models.save_checkin(
        date=today,
        bot_message=bot_message,
        user_response=user_text,
        missed=data.get("missed", []),
        reasons=data.get("reasons", {}),
        sentiment=data.get("sentiment", "neutro")
    )

    sentiment = data.get("sentiment", "neutro")
    if sentiment == "positivo":
        reply = "🌟 Ottima giornata! Continua così, stai costruendo abitudini solide. Buonanotte! 🌙"
    elif sentiment == "negativo":
        reply = "💙 Capita a tutti. L'importante è riconoscerlo e ripartire domani. Buonanotte! 🌙"
    else:
        reply = "👍 Grazie per il resoconto! Ho salvato tutto. Domani è un nuovo giorno. Buonanotte! 🌙"

    await update.message.reply_text(reply)
