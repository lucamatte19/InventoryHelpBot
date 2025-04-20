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
    """Mostra le statistiche di utilizzo personali dei comandi."""
    user = update.effective_user
    username = user.username or f"utente_{user.id}"
    
    # Carica i dati dell'utente
    from utils.player_data import load_player_data
    data = load_player_data(user.id)
    
    if "stats" not in data:
        await update.message.reply_text(f"@{username}, non hai ancora utilizzato alcun comando tracciato!")
        return
    
    stats = data["stats"]
    
    # Verifica che i dati totali siano coerenti (totale >= giornaliero)
    for cmd in stats:
        if stats[cmd].get("total", 0) < stats[cmd].get("today", 0):
            # Correggi il dato nel caso in cui il totale sia inferiore al giornaliero
            stats[cmd]["total"] = stats[cmd]["today"]
    
    # Componi il messaggio di risposta
    reply_text = f"📊 *Statistiche di utilizzo per @{username}* 📊\n\n"
    
    # Comandi avventura
    reply_text += "*Avventura:*\n"
    avventura_stats = stats.get("avventura", {"today": 0, "total": 0})
    reply_text += f"🗡 Oggi: {avventura_stats.get('today', 0)} | Totale: {avventura_stats.get('total', 0)}\n\n"
    
    # Comandi speciali (slot e borsellino)
    reply_text += "*Comandi Speciali:*\n"
    slot_stats = stats.get("slot", {"today": 0, "total": 0})
    reply_text += f"🎰 Slot: {slot_stats.get('today', 0)} oggi | {slot_stats.get('total', 0)} totale\n"
    
    borsellino_stats = stats.get("borsellino", {"today": 0, "total": 0})
    reply_text += f"💰 Borsellino: {borsellino_stats.get('today', 0)} oggi | {borsellino_stats.get('total', 0)} totale\n\n"
    
    # Comandi giornalieri
    reply_text += "*Comandi Giornalieri:*\n"
    
    nanoc_stats = stats.get("nanoc", {"today": 0, "total": 0})
    reply_text += f"🧪 NanoC: {nanoc_stats.get('today', 0)} oggi | {nanoc_stats.get('total', 0)} totale\n"
    
    nanor_stats = stats.get("nanor", {"today": 0, "total": 0})
    reply_text += f"🔄 NanoR: {nanor_stats.get('today', 0)} oggi | {nanor_stats.get('total', 0)} totale\n"
    
    gica_stats = stats.get("gica", {"today": 0, "total": 0})
    reply_text += f"🧙‍♂️ Gica: {gica_stats.get('today', 0)} oggi | {gica_stats.get('total', 0)} totale\n"
    
    pozzo_stats = stats.get("pozzo", {"today": 0, "total": 0})
    reply_text += f"🚰 Pozzo: {pozzo_stats.get('today', 0)} oggi | {pozzo_stats.get('total', 0)} totale\n"
    
    compattatore_stats = stats.get("compattatore", {"today": 0, "total": 0})
    reply_text += f"🗜️ Compattatore: {compattatore_stats.get('today', 0)} oggi | {compattatore_stats.get('total', 0)} totale\n\n"
    
    # Comandi settimanali
    reply_text += "*Comandi Settimanali:*\n"
    
    sonda_stats = stats.get("sonda", {"today": 0, "total": 0})
    reply_text += f"🔍 Sonda: {sonda_stats.get('today', 0)} oggi | {sonda_stats.get('total', 0)} totale\n"
    
    forno_stats = stats.get("forno", {"today": 0, "total": 0})
    reply_text += f"🔥 Forno: {forno_stats.get('today', 0)} oggi | {forno_stats.get('total', 0)} totale\n\n"
    
    reply_text += "Usa /siutilizzi per ricevere automaticamente queste statistiche ogni giorno a mezzanotte."
    
    # Invia la risposta
    await update.message.reply_text(reply_text, parse_mode="Markdown")

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
