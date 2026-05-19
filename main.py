"""
main.py — Entry point del Bot Assistente Personale.

Avvio:
    python main.py
"""
import logging
import asyncio
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_TOKEN, validate_config
from database.db import init_db
from bot.handlers.commands import (
    start_handler,
    help_handler,
    agenda_oggi_handler,
    settimana_handler,
)
from bot.handlers.messages import message_handler
from services.scheduler import setup_scheduler

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)   # silenzia i log HTTP
logger = logging.getLogger(__name__)

async def post_init(app):
    setup_scheduler(app)
def main():
    logger.info("🚀 Avvio Bot Assistente Personale...")

    # 1. Valida configurazione
    if not validate_config():
        logger.error("❌ Configurazione non valida. Controlla il file .env")
        sys.exit(1)

    # 2. Inizializza il database SQLite
    init_db()

    # 3. Crea l'applicazione Telegram
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init).build()
    )

    # 4. Registra i command handler
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("agenda", agenda_oggi_handler))
    app.add_handler(CommandHandler("settimana", settimana_handler))

    # 5. Registra il message handler (linguaggio naturale)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_handler
    ))

    # 6. Avvia lo scheduler (check-in serale, report settimanale)
    

    logger.info("✅ Bot pronto! In ascolto su Telegram...")

    # 7. Avvia il polling
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True   # ignora messaggi arrivati mentre era offline
    )


if __name__ == "__main__":
    main()
