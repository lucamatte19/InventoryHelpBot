import time
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from utils.player_data import (
    load_player_data, update_player_notification_setting, 
    update_daily_stats_subscription, update_startup_notification_setting,
    get_startup_notification_status
)
from utils.timer_data import TIMER_DATA

async def impostazioni_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra e gestisce le impostazioni dell'utente."""
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user_id}"
    
    player_data = load_player_data(user_id)
    notification_settings = player_data["settings"]["notifications"]
    daily_stats_enabled = player_data["settings"].get("daily_stats", False)
    startup_notify_enabled = player_data["settings"].get("startup_notifications", True)
    
    # Prepara il messaggio con le impostazioni attuali
    response_lines = [f"⚙️ *Impostazioni di @{username}* ⚙️\n"]
    
    # Notifiche per i vari comandi
    response_lines.append("🔔 *Notifiche Comandi:*")
    for command, enabled in notification_settings.items():
        if command in TIMER_DATA:
            emoji = TIMER_DATA[command]["emoji"]
            status = "✅ Attive" if enabled else "❌ Disattivate"
            response_lines.append(f"{emoji} *{command.capitalize()}*: {status}")
    
    # Statistiche giornaliere
    response_lines.append("\n📊 *Statistiche Giornaliere:*")
    stats_status = "✅ Attive" if daily_stats_enabled else "❌ Disattivate"
    response_lines.append(f"Notifiche statistiche giornaliere: {stats_status}")
    
    # Notifiche di avvio
    response_lines.append("\n🚀 *Notifiche di Sistema:*")
    startup_status = "✅ Attive" if startup_notify_enabled else "❌ Disattivate"
    response_lines.append(f"Notifiche all'avvio del bot: {startup_status}")
    
    # Info registrazione
    register_date = datetime.datetime.fromtimestamp(player_data["register_date"])
    response_lines.append(f"\n📆 *Registrato dal:* {register_date.strftime('%d/%m/%Y')}")
    
    # Pulsanti per modificare le impostazioni
    keyboard = []
    
    # Riga 1: Toggle notifiche comandi principali
    row1 = []
    for command in ["avventura", "slot", "borsellino"]:
        if command in notification_settings:
            emoji = "🔔" if notification_settings[command] else "🔕"
            row1.append(InlineKeyboardButton(
                f"{emoji} {command.capitalize()}", 
                callback_data=f"toggle_notif_{command}"
            ))
    keyboard.append(row1)
    
    # Riga 2: Toggle notifiche oggetti giornalieri
    row2 = []
    for command in ["nanoc", "nanor", "gica", "pozzo"]:
        if command in notification_settings:
            emoji = "🔔" if notification_settings[command] else "🔕"
            row2.append(InlineKeyboardButton(
                f"{emoji} {command.capitalize()}", 
                callback_data=f"toggle_notif_{command}"
            ))
    keyboard.append(row2)
    
    # Riga 3: Toggle notifiche oggetti settimanali
    row3 = []
    for command in ["sonda", "forno"]:
        if command in notification_settings:
            emoji = "🔔" if notification_settings[command] else "🔕"
            row3.append(InlineKeyboardButton(
                f"{emoji} {command.capitalize()}", 
                callback_data=f"toggle_notif_{command}"
            ))
    keyboard.append(row3)
    
    # Riga 4: Toggle statistiche giornaliere e notifiche di avvio
    row4 = [
        InlineKeyboardButton(
            f"{'✅' if daily_stats_enabled else '❌'} Stats Giornaliere", 
            callback_data="toggle_daily_stats"
        ),
        InlineKeyboardButton(
            f"{'✅' if startup_notify_enabled else '❌'} Notifiche Avvio", 
            callback_data="toggle_startup_notify"
        )
    ]
    keyboard.append(row4)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "\n".join(response_lines),
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def impostazioni_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce le callback dei pulsanti delle impostazioni."""
    query = update.callback_query
    user_id = update.effective_user.id
    callback_data = query.data
    
    # Fornisci un feedback immediato che il comando è stato ricevuto
    await query.answer("Aggiornamento impostazioni...")
    
    try:
        if callback_data.startswith("toggle_notif_"):
            command = callback_data.replace("toggle_notif_", "")
            player_data = load_player_data(user_id)
            current_setting = player_data["settings"]["notifications"].get(command, True)
            
            # Aggiorna l'impostazione (inverti il valore corrente)
            update_player_notification_setting(user_id, command, not current_setting)
            
            # Fornisci un feedback specifico
            status = "attivate" if not current_setting else "disattivate"
            await query.answer(f"Notifiche {command} {status}", show_alert=False)
            
        elif callback_data == "toggle_daily_stats":
            player_data = load_player_data(user_id)
            current_setting = player_data["settings"].get("daily_stats", False)
            
            # Aggiorna l'impostazione
            update_daily_stats_subscription(user_id, not current_setting)
            
            # Fornisci un feedback specifico
            status = "attivate" if not current_setting else "disattivate"
            await query.answer(f"Statistiche giornaliere {status}", show_alert=False)
            
        elif callback_data == "toggle_startup_notify":
            current_setting = get_startup_notification_status(user_id)
            
            # Aggiorna l'impostazione
            update_startup_notification_setting(user_id, not current_setting)
            
            # Fornisci un feedback specifico
            status = "attivate" if not current_setting else "disattivate"
            await query.answer(f"Notifiche di avvio {status}", show_alert=False)
    except Exception as e:
        print(f"Errore durante l'elaborazione della callback: {e}")
        await query.answer("Si è verificato un errore", show_alert=True)
    
    # Aggiorna il messaggio con le nuove impostazioni
    # NON chiamare impostazioni_command che causa errore con callback
    try:
        username = update.effective_user.username or f"utente_{user_id}"
        player_data = load_player_data(user_id)
        notification_settings = player_data["settings"]["notifications"]
        daily_stats_enabled = player_data["settings"].get("daily_stats", False)
        startup_notify_enabled = player_data["settings"].get("startup_notifications", True)
        
        # Prepara il messaggio con le impostazioni attuali
        response_lines = [f"⚙️ *Impostazioni di @{username}* ⚙️\n"]
        
        # Notifiche per i vari comandi
        response_lines.append("🔔 *Notifiche Comandi:*")
        for command, enabled in notification_settings.items():
            if command in TIMER_DATA:
                emoji = TIMER_DATA[command]["emoji"]
                status = "✅ Attive" if enabled else "❌ Disattivate"
                response_lines.append(f"{emoji} *{command.capitalize()}*: {status}")
        
        # Statistiche giornaliere
        response_lines.append("\n📊 *Statistiche Giornaliere:*")
        stats_status = "✅ Attive" if daily_stats_enabled else "❌ Disattivate"
        response_lines.append(f"Notifiche statistiche giornaliere: {stats_status}")
        
        # Notifiche di avvio
        response_lines.append("\n🚀 *Notifiche di Sistema:*")
        startup_status = "✅ Attive" if startup_notify_enabled else "❌ Disattivate"
        response_lines.append(f"Notifiche all'avvio del bot: {startup_status}")
        
        # Info registrazione
        register_date = datetime.datetime.fromtimestamp(player_data["register_date"])
        response_lines.append(f"\n📆 *Registrato dal:* {register_date.strftime('%d/%m/%Y')}")
        
        # Pulsanti per modificare le impostazioni
        keyboard = []
        
        # Riga 1: Toggle notifiche comandi principali
        row1 = []
        for command in ["avventura", "slot", "borsellino"]:
            if command in notification_settings:
                emoji = "🔔" if notification_settings[command] else "🔕"
                row1.append(InlineKeyboardButton(
                    f"{emoji} {command.capitalize()}", 
                    callback_data=f"toggle_notif_{command}"
                ))
        keyboard.append(row1)
        
        # Riga 2: Toggle notifiche oggetti giornalieri
        row2 = []
        for command in ["nanoc", "nanor", "gica", "pozzo"]:
            if command in notification_settings:
                emoji = "🔔" if notification_settings[command] else "🔕"
                row2.append(InlineKeyboardButton(
                    f"{emoji} {command.capitalize()}", 
                    callback_data=f"toggle_notif_{command}"
                ))
        keyboard.append(row2)
        
        # Riga 3: Toggle notifiche oggetti settimanali
        row3 = []
        for command in ["sonda", "forno"]:
            if command in notification_settings:
                emoji = "🔔" if notification_settings[command] else "🔕"
                row3.append(InlineKeyboardButton(
                    f"{emoji} {command.capitalize()}", 
                    callback_data=f"toggle_notif_{command}"
                ))
        keyboard.append(row3)
        
        # Riga 4: Toggle statistiche giornaliere e notifiche di avvio
        row4 = [
            InlineKeyboardButton(
                f"{'✅' if daily_stats_enabled else '❌'} Stats Giornaliere", 
                callback_data="toggle_daily_stats"
            ),
            InlineKeyboardButton(
                f"{'✅' if startup_notify_enabled else '❌'} Notifiche Avvio", 
                callback_data="toggle_startup_notify"
            )
        ]
        keyboard.append(row4)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Modifica il messaggio esistente invece di inviarne uno nuovo
        await query.edit_message_text(
            "\n".join(response_lines),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Errore nell'aggiornamento del messaggio delle impostazioni: {e}")
        await query.answer("Errore nell'aggiornamento della vista", show_alert=True)

def register_impostazioni_handlers(app):
    """Registra gli handler per il comando impostazioni."""
    from telegram.ext import CommandHandler
    
    app.add_handler(CommandHandler("impostazioni", impostazioni_command))
    app.add_handler(CallbackQueryHandler(impostazioni_callback, pattern=r'^toggle_'))
