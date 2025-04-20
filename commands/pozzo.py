import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    pozzo_times, active_pozzo_tasks, disabled_pozzo, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per pozzo
pozzo_handler = TimerHandler("pozzo")

async def handle_pozzo_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa pozzo."""
    regex_pattern = r'^/usa\s+pozzo(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await pozzo_handler.handle_command(update, context, match)

async def toggle_pozzo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per pozzo."""
    await pozzo_handler.toggle_notifications(update, context)
