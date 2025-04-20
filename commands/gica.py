import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    gica_times, active_gica_tasks, disabled_gica, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per gica
gica_handler = TimerHandler("gica")

async def handle_gica_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa gica."""
    regex_pattern = r'^/usa\s+gica(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await gica_handler.handle_command(update, context, match)

async def toggle_gica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per gica."""
    await gica_handler.toggle_notifications(update, context)
