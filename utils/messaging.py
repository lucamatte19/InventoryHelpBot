import logging
from telegram import Update
from telegram.ext import ApplicationBuilder
from utils.timer_data import TOKEN

logger = logging.getLogger(__name__)

async def send_notification(update: Update, user_id: int, username: str, message: str, command_name: str):
    """
    Invia una notifica all'utente, provando prima a rispondere al messaggio originale.
    Se fallisce, invia un messaggio diretto.
    
    Args:
        update: L'oggetto Update originale, che potrebbe non essere più valido dopo un riavvio
        user_id: L'ID dell'utente a cui inviare la notifica
        username: Il nome utente per la menzione
        message: Il messaggio da inviare
        command_name: Il nome del comando per il logging
    """
    try:
        # Prima prova a rispondere al messaggio originale
        await update.message.reply_text(message)
        logger.info(f"[{command_name}] Notification sent as reply to user {user_id}")
    except Exception as reply_error:
        # Se fallisce (probabilmente perché il bot è stato riavviato), invia un messaggio diretto
        logger.warning(f"[{command_name}] Could not reply to original message: {reply_error}")
        logger.info(f"[{command_name}] Sending direct message instead")
        
        try:
            # Crea un'istanza temporanea del bot
            temp_app = ApplicationBuilder().token(TOKEN).build()
            await temp_app.bot.send_message(
                chat_id=user_id,
                text=message
            )
            logger.info(f"[{command_name}] Direct notification sent to user {user_id}")
        except Exception as send_error:
            logger.error(f"[{command_name}] Error sending direct message: {send_error}")
            return False
    
    return True

async def send_direct_message(user_id: int, message: str, command_name: str):
    """
    Invia un messaggio diretto all'utente senza tentare di rispondere a un messaggio precedente.
    Utile per timer che erano attivi prima del riavvio del bot.
    
    Args:
        user_id: L'ID dell'utente a cui inviare la notifica
        message: Il messaggio da inviare
        command_name: Il nome del comando per il logging
    """
    try:
        # Crea un'istanza temporanea del bot
        temp_app = ApplicationBuilder().token(TOKEN).build()
        await temp_app.bot.send_message(
            chat_id=user_id,
            text=message
        )
        logger.info(f"[{command_name}] Direct message sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"[{command_name}] Error sending direct message to user {user_id}: {e}")
        return False
