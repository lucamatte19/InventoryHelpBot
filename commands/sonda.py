import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    sonda_times, active_sonda_tasks, disabled_sonda, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per sonda
sonda_handler = TimerHandler("sonda")

async def handle_sonda_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa sonda."""
    regex_pattern = r'^/usa\s+sonda(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await sonda_handler.handle_command(update, context, match)

async def toggle_sonda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per sonda."""
    await sonda_handler.toggle_notifications(update, context)
