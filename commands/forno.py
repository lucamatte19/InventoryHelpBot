import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    forno_times, active_forno_tasks, disabled_forno, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per forno
forno_handler = TimerHandler("forno")

async def handle_forno_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa forno."""
    regex_pattern = r'^/usa\s+forno(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await forno_handler.handle_command(update, context, match)

async def toggle_forno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per forno."""
    await forno_handler.toggle_notifications(update, context)
