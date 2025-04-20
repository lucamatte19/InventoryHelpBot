import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    nanoc_times, active_nanoc_tasks, disabled_nanoc, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per nanoc
nanoc_handler = TimerHandler("nanoc")

async def handle_nanoc_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa nanoc."""
    print(f"[Nanoc] Received: '{update.message.text}'")
    regex_pattern = r'^/usa\s+nanoc(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        print("[Nanoc] Regex did not match.")
        return

    await nanoc_handler.handle_command(update, context, match)

async def toggle_nanoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per nanoc."""
    await nanoc_handler.toggle_notifications(update, context)
