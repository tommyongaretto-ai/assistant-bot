"""
bot/handlers/commands.py — Handler per i comandi /start, /help, /agenda, ecc.
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from database import models


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.effective_user.first_name or "amico"
    testo = (
        f"👋 Ciao {nome}! Sono il tuo *Assistente Personale AI*.\n\n"
        "Posso aiutarti con:\n"
        "📅 *Agenda* — scrivi in modo naturale\n"
        "   _Es: 'Domani alle 10 ho una riunione di lavoro'_\n\n"
        "🍝 *Diario alimentare* — registra i pasti\n"
        "   _Es: 'A pranzo pasta al pomodoro e una mela'_\n\n"
        "⚽ *Partite del Milan* — le inserisco io!\n\n"
        "🌙 *Check-in serale* — ogni sera alle 22:00\n\n"
        "🧠 *Report settimanale* — ogni domenica\n\n"
        "Parlami liberamente, capisco il linguaggio naturale!\n"
        "Usa /help per vedere tutti i comandi."
    )
    await update.message.reply_text(testo, parse_mode="Markdown")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = (
        "📖 *Comandi disponibili:*\n\n"
        "/start — Messaggio di benvenuto\n"
        "/agenda — Impegni di oggi\n"
        "/settimana — Impegni della settimana\n"
        "/report — Richiedi report manuale\n"
        "/help — Questo messaggio\n\n"
        "💬 *Esempi linguaggio naturale:*\n"
        "• 'Domani alle 9 ho una visita medica'\n"
        "• 'Stasera palestra dalle 19 alle 20:30'\n"
        "• 'A cena cotoletta con patatine'\n"
        "• 'Cosa ho in agenda domani?'\n"
        "• 'Sposta la riunione alle 15'\n"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")


async def agenda_oggi_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    events = models.get_events_for_date(today)

    if not events:
        await update.message.reply_text("📅 Nessun impegno programmato per oggi.")
        return

    righe = [f"📅 *Agenda di oggi — {datetime.now().strftime('%d/%m/%Y')}*\n"]
    for e in events:
        ora_inizio = e["start_datetime"][11:16]
        ora_fine = e["end_datetime"][11:16]
        emoji = _emoji_categoria(e["category"])
        righe.append(f"{emoji} *{e['title']}*\n   🕐 {ora_inizio} → {ora_fine}")

    await update.message.reply_text("\n".join(righe), parse_mode="Markdown")


async def settimana_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oggi = datetime.now()
    lunedi = oggi - timedelta(days=oggi.weekday())
    domenica = lunedi + timedelta(days=6)

    events = models.get_events_for_week(
        lunedi.strftime("%Y-%m-%d"),
        domenica.strftime("%Y-%m-%d")
    )

    if not events:
        await update.message.reply_text("📅 Nessun impegno questa settimana.")
        return

    giorni = {}
    for e in events:
        giorno = e["start_datetime"][:10]
        giorni.setdefault(giorno, []).append(e)

    righe = ["📅 *Agenda della settimana:*\n"]
    for giorno, ev_list in sorted(giorni.items()):
        data_fmt = datetime.strptime(giorno, "%Y-%m-%d").strftime("%A %d/%m")
        righe.append(f"\n*{data_fmt.capitalize()}*")
        for e in ev_list:
            ora = e["start_datetime"][11:16]
            emoji = _emoji_categoria(e["category"])
            righe.append(f"  {emoji} {ora} — {e['title']}")

    await update.message.reply_text("\n".join(righe), parse_mode="Markdown")


def _emoji_categoria(category: str) -> str:
    mappa = {
        "lavoro": "💼",
        "sport": "🏋️",
        "salute": "🏥",
        "personale": "👤",
        "sport_milan": "⚽",
    }
    return mappa.get(category, "📌")
