import logging
from telegram import Update
from telegram.ext import ApplicationBuilder
from utils.timer_data import TOKEN
from telegram.ext import ContextTypes
from utils.player_data import get_preferred_notification_chat
from utils.logger import logger

logger = logging.getLogger(__name__)

async def send_notification(update, user_id, username, message, command_name=None):
    """Invia una notifica all'utente, usando la chat preferita se impostata."""
    try:
        # Ottieni la chat preferita (se impostata, altrimenti usa la chat utente)
        preferred_chat_id = get_preferred_notification_chat(user_id)
        
        # Se non c'è una chat preferita, usa la chat utente direttamente
        chat_id = preferred_chat_id if preferred_chat_id else user_id
        
        # Invia il messaggio alla chat appropriata
        await update.get_bot().send_message(
            chat_id=chat_id,
            text=message
        )
        
        if command_name:
            logger.info(f"[{command_name}] Notification sent to user {user_id} in chat {chat_id}")
        
        return True
    except Exception as e:
        if command_name:
            logger.error(f"[{command_name}] Error sending notification to user {user_id}: {e}")
        return False

async def send_direct_message(user_id, message, command_name=None):
    """Invia un messaggio diretto all'utente, usando la chat preferita se impostata."""
    try:
        from telegram.ext import ApplicationBuilder
        from utils.timer_data import TOKEN
        
        # Ottieni la chat preferita (se impostata, altrimenti usa la chat utente)
        preferred_chat_id = get_preferred_notification_chat(user_id) 
        
        # Se non c'è una chat preferita, usa la chat utente direttamente
        chat_id = preferred_chat_id if preferred_chat_id else user_id
        
        # Crea un'applicazione temporanea
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Invia il messaggio alla chat appropriata
        await app.bot.send_message(
            chat_id=chat_id,
            text=message
        )
        
        if command_name:
            logger.info(f"[{command_name}] Direct message sent to user {user_id} in chat {chat_id}")
        
        return True
    except Exception as e:
        if command_name:
            logger.error(f"[{command_name}] Error sending direct message to user {user_id}: {e}")
        return False
