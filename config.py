"""
config.py — Configurazione centralizzata del bot.
Tutti i parametri vengono letti dal file .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
YOUR_CHAT_ID: int = int(os.getenv("YOUR_CHAT_ID", "0"))

# ── AI ────────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")     # per Whisper

# ── Sport ─────────────────────────────────────────────────────────────────────
API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")
MILAN_TEAM_ID: int = 489          # ID del Milan su API-Football
MILAN_LEAGUE_ID: int = 135        # Serie A

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = "data/assistant.db"

# ── Scheduler ─────────────────────────────────────────────────────────────────
CHECKIN_HOUR: int = int(os.getenv("CHECKIN_HOUR", "22"))
CHECKIN_MINUTE: int = int(os.getenv("CHECKIN_MINUTE", "0"))

# ── Sanity check all'avvio ────────────────────────────────────────────────────
def validate_config() -> bool:
    """Controlla che le variabili obbligatorie siano presenti."""
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if not YOUR_CHAT_ID:
        missing.append("YOUR_CHAT_ID")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print(f"❌ Variabili mancanti nel .env: {', '.join(missing)}")
        return False

    print("✅ Configurazione valida")
    return True
