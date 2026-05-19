import logging
from datetime import time
from config import YOUR_CHAT_ID, CHECKIN_HOUR, CHECKIN_MINUTE
from database import models
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def _job_evening_checkin(context):
    from bot.handlers.messages import set_awaiting_checkin
    today = datetime.now().strftime("%Y-%m-%d")
    events = models.get_events_for_date(today)
    data_fmt = datetime.now().strftime("%d/%m/%Y")
    if events:
        lista = "\n".join([f"• {e['title']} ({e['start_datetime'][11:16]})" for e in events])
        msg = f"🌙 *Buonanotte! Riepilogo di oggi — {data_fmt}*\n\n{lista}\n\nCome è andata?"
    else:
        msg = f"🌙 *Buonanotte! — {data_fmt}*\n\nCome è andata la giornata?"
    await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=msg, parse_mode="Markdown")
    set_awaiting_checkin(YOUR_CHAT_ID, msg)

async def _job_weekly_report(context):
    await context.bot.send_message(chat_id=YOUR_CHAT_ID, text="📊 Report settimanale in arrivo!")

def setup_scheduler(app):
    jq = app.job_queue
    jq.run_daily(_job_evening_checkin, time=time(hour=CHECKIN_HOUR, minute=CHECKIN_MINUTE), name="checkin")
    jq.run_daily(_job_weekly_report, time=time(hour=10, minute=0), days=(6,), name="report")
    logger.info("⏰ Scheduler avviato")