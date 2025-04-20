import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    avventura_times, active_avventura_tasks, disabled_avventura, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats qui
)
from utils.messaging import send_notification

async def check_cooldown_avventura(user_id: int) -> bool:
    now = time.time()
    last_time = avventura_times.get(user_id, 0)
    return now - last_time >= COOLDOWNS["avventura"]

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per avventura
avventura_handler = TimerHandler("avventura")

async def handle_avventura_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /avventura."""
    regex_pattern = r'^/avventura(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        return

    await avventura_handler.handle_command(update, context, match)

async def toggle_avventura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per avventura."""
    await avventura_handler.toggle_notifications(update, context)
