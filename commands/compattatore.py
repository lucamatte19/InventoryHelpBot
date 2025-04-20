import re
from telegram import Update
from telegram.ext import ContextTypes

from utils.timer_handler import TimerHandler

# Crea un'istanza dell'handler per il compattatore
compattatore_handler = TimerHandler("compattatore")

async def handle_compattatore_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /usa compattatore."""
    print(f"[Compattatore] Received: '{update.message.text}'")
    regex_pattern = r'^/usa\s+(?:compattatore|comp)(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        print("[Compattatore] Regex did not match.")
        return

    await compattatore_handler.handle_command(update, context, match)

async def toggle_compattatore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche per il compattatore."""
    await compattatore_handler.toggle_notifications(update, context)
