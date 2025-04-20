import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    nanor_times, active_nanor_tasks, disabled_nanor, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per nanor
nanor_handler = TimerHandler("nanor")

async def handle_nanor_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa nanor."""
    regex_pattern = r'^/usa\s+nanor(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await nanor_handler.handle_command(update, context, match)

async def toggle_nanor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per nanor."""
    await nanor_handler.toggle_notifications(update, context)
