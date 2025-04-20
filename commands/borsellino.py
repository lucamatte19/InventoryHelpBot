import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    borsellino_times, active_borsellino_tasks, disabled_borsellino, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats
)
from utils.messaging import send_notification
from utils.logger import logger

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per borsellino
borsellino_handler = TimerHandler("borsellino")

async def handle_borsellino_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa borsellino."""
    regex_pattern = r'^/usa\s+(?:borsellino|borse|bors|sel|sell|sellino)(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await borsellino_handler.handle_command(update, context, match)

async def toggle_borsellino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per borsellino."""
    await borsellino_handler.toggle_notifications(update, context)
