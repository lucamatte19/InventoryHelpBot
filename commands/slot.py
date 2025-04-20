import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    slot_times, active_slot_tasks, disabled_slot, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats
)
from utils.messaging import send_notification

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per slot
slot_handler = TimerHandler("slot")

async def handle_slot_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa slot."""
    regex_pattern = r'^/usa\s+(?:sl|slo|slot)(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await slot_handler.handle_command(update, context, match)

async def toggle_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per slot."""
    await slot_handler.toggle_notifications(update, context)
