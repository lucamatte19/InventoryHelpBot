import asyncio
import datetime
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time
from utils.timer_data import (
    TIMER_DATA, daily_stats
)
from utils.player_data import (
    load_player_data, update_daily_stats_subscription,
    get_all_subscribes_users, update_username
)

async def handle_utilizzi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra le statistiche di utilizzo personali dell'utente."""
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user_id}"
    
    # Aggiorna username se disponibile
    if username != f"utente_{user_id}":
        update_username(user_id, username)
    
    # Ottieni le statistiche dell'utente dalla nuova struttura dati persistente
    player_data = load_player_data(user_id)
    stats = player_data["stats"]
    
    response_lines = [f"📊 *Statistiche di utilizzo per @{username}* 📊"]
    
    today = datetime.datetime.now().strftime("%d/%m/%Y")
    response_lines.append(f"📅 *Data*: {today}")
    
    # Statistiche per ogni comando supportato
    for command in ["avventura", "slot", "borsellino", "nanoc", "nanor", "gica", "pozzo", "sonda", "forno"]:
        emoji = TIMER_DATA[command]["emoji"]
        count_today = stats.get(command, {}).get("today", 0)
        count_total = stats.get(command, {}).get("total", 0)
        response_lines.append(f"{emoji} *{command.capitalize()}*: {count_today} oggi, {count_total} totali")
    
    # Aggiungi info sul servizio di notifiche giornaliere
    daily_stats_enabled = player_data["settings"].get("daily_stats", False)
    if daily_stats_enabled:
        response_lines.append("\n✅ *Notifiche giornaliere*: Attive")
        response_lines.append("Riceverai un resoconto dei tuoi utilizzi ogni giorno a mezzanotte.")
        response_lines.append("Usa /noutilizzi per disattivarle.")
    else:
        response_lines.append("\n❌ *Notifiche giornaliere*: Disattivate")
        response_lines.append("Usa /siutilizzi per ricevere un resoconto dei tuoi utilizzi ogni giorno a mezzanotte.")
    
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

async def toggle_utilizzi_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche giornaliere degli utilizzi."""
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user_id}"
    
    player_data = load_player_data(user_id)
    current_setting = player_data["settings"].get("daily_stats", False)
    
    # Inverti l'impostazione
    update_daily_stats_subscription(user_id, not current_setting)
    
    if current_setting:
        await update.message.reply_text(
            f"@{username}, ho disattivato le notifiche giornaliere delle statistiche di utilizzo."
        )
    else:
        await update.message.reply_text(
            f"@{username}, ho attivato le notifiche giornaliere delle statistiche di utilizzo. "
            f"Riceverai un resoconto ogni giorno a mezzanotte."
        )

async def send_daily_personal_stats(context):
    """Invia le statistiche personali agli utenti iscritti."""
    subscribed_users = get_all_subscribes_users()
    
    now = datetime.datetime.now()
    today = now.strftime("%d/%m/%Y")
    
    print(f"Invio statistiche giornaliere personali a {len(subscribed_users)} utenti...")
    sent_count = 0
    error_count = 0
    
    for user_id in subscribed_users:
        player_data = load_player_data(user_id)
        stats = player_data["stats"]
        username = player_data.get("username", "") or f"utente_{user_id}"
        
        response_lines = [f"📊 *Statistiche di utilizzo giornaliere* 📊"]
        response_lines.append(f"📅 *Data*: {today}")
        
        # Stats for each command
        has_activity = False
        for command in ["avventura", "slot", "borsellino", "nanoc", "nanor", "gica", "pozzo", "sonda", "forno"]:
            emoji = TIMER_DATA[command]["emoji"]
            count = stats.get(command, {}).get("today", 0)
            if count > 0:
                has_activity = True
            response_lines.append(f"{emoji} *{command.capitalize()}*: {count} utilizzi oggi")
        
        if not has_activity:
            response_lines.append("\n❓ *Nessuna attività registrata oggi*")
            
        response_lines.append("\nPuoi disattivare queste notifiche con /noutilizzi")
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="\n".join(response_lines),
                parse_mode="Markdown"
            )
            sent_count += 1
            # Breve pausa per evitare di raggiungere limiti di rate
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Errore nell'invio delle statistiche personali all'utente {user_id}: {e}")
            error_count += 1
    
    print(f"Statistiche personali inviate: {sent_count} successi, {error_count} errori")
