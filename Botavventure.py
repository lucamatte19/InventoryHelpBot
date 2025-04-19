from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import asyncio
import re
import time
import configparser
import os
import datetime

# Importa le utility
from utils.timer_data import (
    TIMER_DATA, config, config_path, ADMIN_USERNAME, 
    daily_stats, TOKEN, registered_users, save_registered_users,
    user_stats, disabled_avventura, disabled_slot, disabled_borsellino,
    disabled_nanoc, disabled_nanor, disabled_gica, disabled_pozzo,
    disabled_sonda, disabled_forno
)
from utils.formatters import format_remaining_time
from utils.player_data import (
    migrate_existing_data, get_all_subscribes_users,
    load_player_data, reset_daily_stats
)

# Importa i comandi
from commands.avventura import (
    handle_avventura_mention, toggle_avventura
)
from commands.slot import (
    handle_slot_mention, toggle_slot
)
from commands.borsellino import (
    handle_borsellino_mention, toggle_borsellino
)
from commands.nanoc import (
    handle_nanoc_mention, toggle_nanoc
)
from commands.nanor import (
    handle_nanor_mention, toggle_nanor
)
from commands.gica import (
    handle_gica_mention, toggle_gica
)
from commands.pozzo import (
    handle_pozzo_mention, toggle_pozzo
)
from commands.sonda import (
    handle_sonda_mention, toggle_sonda
)
from commands.forno import (
    handle_forno_mention, toggle_forno
)
from commands.utilizzi import (
    handle_utilizzi_command, toggle_utilizzi_notifications, send_daily_personal_stats
)
from commands.admin import register_admin_handlers
from commands.impostazioni import register_impostazioni_handlers, impostazioni_command

# Gestione timer
async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra i timer rimanenti per l'utente che esegue il comando."""
    user_id = update.effective_user.id
    username = update.effective_user.username or f"utente_{user_id}"
    now = time.time()
    
    response_lines = [f"⏱️ *Timer per @{username}* ⏱️"]
    
    # Iterate through the defined timers
    for item_name, data in TIMER_DATA.items():
        times_dict = data["times"]
        active_tasks_dict = data["active"]
        max_cooldown = data["cooldown"]
        emoji = data["emoji"]
        
        # Controlla se l'utente ha un task attivo per questo comando
        has_active_task = user_id in active_tasks_dict
        last_start_time = times_dict.get(user_id, 0)
        
        if last_start_time == 0:
            # Nessun timer mai usato
            status = "✅ Disponibile"
        else:
            # Calcola il tempo rimanente, sia per timer attivi che per quelli in cooldown
            elapsed = now - last_start_time
            remaining_seconds = max(0, int(max_cooldown - elapsed))
            
            if remaining_seconds > 0:
                # Timer in corso (sia attivo che in cooldown)
                status = f"⏳ {format_remaining_time(remaining_seconds)}"
                if has_active_task:
                    status += " (notifica attiva)"
            else:
                # Timer completato
                status = "✅ Disponibile"
                
        response_lines.append(f"{emoji} *{item_name.capitalize()}*: {status}")
        
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

# Funzione per inviare le statistiche giornaliere
async def send_daily_stats(context: ContextTypes.DEFAULT_TYPE):
    if 'stats' not in config or 'recipient_chat_id' not in config['stats']:
        print("Nessun destinatario impostato per le statistiche")
        return
    
    # ... Implementazione delle statistiche giornaliere ...
    # ...existing code...

# Comando start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start e registra l'utente."""
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user_id}"
    
    # Registra l'utente se non è già registrato
    if user_id not in registered_users:
        registered_users.add(user_id)
        save_registered_users()
        print(f"Nuovo utente registrato: {username} (ID: {user_id})")
    
    welcome_message = (
        f"Ciao {user.mention_html()}! 👋\n\n"
        "Sono **InventoryHelpBot**, un bot che ti aiuta a tenere traccia dei timer per Inventory.\n\n"
        "Usa /info per vedere tutti i comandi disponibili e /timer per controllare i tuoi timer attivi.\n\n"
        "Ti avviserò quando i tuoi timer saranno pronti, così potrai usare i comandi al momento giusto! ⏱️"
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")

# Notifica all'avvio del bot
async def send_startup_notifications(app: Application):
    """Sends a notification to registered chats upon bot startup."""
    startup_message = (
        "🔄 *Bot appena avviato!* 🔄\n\n"
        "Sono tornato online e pronto ad aiutarti.\n"
        "Da ora tutti i timer rimangono correttamente (si spera) salvati senza bisogno che tu modifichi nulla.\n"
        "Usa /timer per controllare i tuoi timer attuali.\n"
        "Usa /impostazioni per personalizzare le tue preferenze.(probabilmente ti conviene disattivare questo messaggio)\n"
        "Se hai idee per comandi da aggiungere o miglioramenti, contatta @LucaQuelloFigo.\n\n"
    )
    
    # Importa la funzione per verificare le preferenze dell'utente
    from utils.player_data import get_startup_notification_status
    
    # Invia la notifica a tutti gli utenti registrati che hanno attivato le notifiche di avvio
    bot = app.bot
    sent_count = 0
    skipped_count = 0
    error_count = 0
    
    print(f"Preparazione notifica di avvio per {len(registered_users)} utenti...")
    
    for user_id in registered_users:
        try:
            # Controlla se l'utente vuole ricevere notifiche di avvio
            if get_startup_notification_status(user_id):
                await bot.send_message(
                    chat_id=user_id,
                    text=startup_message,
                    parse_mode="Markdown"
                )
                sent_count += 1
            else:
                skipped_count += 1
                print(f"Notifica saltata per utente {user_id} (preferenza disattivata)")
        except Exception as e:
            print(f"Errore nell'invio della notifica di avvio all'utente {user_id}: {e}")
            error_count += 1
    
    print(f"Notifiche di avvio: {sent_count} inviate, {skipped_count} saltate, {error_count} errori")

async def post_init(app: Application):
    """Runs after the application has been initialized."""
    # Migrazione dei dati esistenti alle nuove strutture
    disabled_commands = {
        "avventura": disabled_avventura,
        "slot": disabled_slot,
        "borsellino": disabled_borsellino,
        "nanoc": disabled_nanoc,
        "nanor": disabled_nanor,
        "gica": disabled_gica,
        "pozzo": disabled_pozzo,
        "sonda": disabled_sonda,
        "forno": disabled_forno
    }
    
    # Questa funzione ora include anche sync_timers_from_files() e recreate_active_timers()
    try:
        await migrate_existing_data(registered_users, disabled_commands, user_stats, TIMER_DATA)
    except Exception as e:
        print(f"Errore durante la migrazione dei dati: {e}")
        import traceback
        traceback.print_exc()
    
    # Invio notifiche di avvio
    await send_startup_notifications(app)

# Comando info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
✨ **InventoryHelpBot** ✨

⚙️ *Funzionamento Generale*
• I comandi avviano un timer standard
• Per modificare un timer attivo, aggiungi il tempo:
  • Formato breve: `/comando mm:ss` (minuti:secondi)
  • Formato esteso: `/comando hh:mm:ss` (ore:minuti:secondi)
  • Per settimanali: `/comando dd:hh:mm:ss` (giorni:ore:min:sec)
• Disattiva le notifiche con `/nocomando`

⏱️ *Comandi Disponibili*

🗡 *Avventura* (cooldown: 15 min)
`/avventura` - Avvia avventura
`/noavventura` - Toggle notifiche

💰 *Speciali*
`/usa slot` - Slot machine (cooldown: 5 min)
`/noslot` - Toggle notifiche

`/usa borsellino` - Borsellino (cooldown: 30 min)
`/noborsellino` - Toggle notifiche

📅 *Oggetti Giornalieri* (cooldown: 24 ore)
`/usa nanoc` - Impianto nanoreplicante 
`/nonanoc` - Toggle notifiche

`/usa nanor` - Nanoreplicante
`/nonanor` - Toggle notifiche

`/usa gica` - Piantina magica
`/nogica` - Toggle notifiche

`/usa pozzo` - Pozzo
`/nopozzo` - Toggle notifiche

📆 *Oggetti Settimanali* (cooldown: 7 giorni)
`/usa sonda` - Sonda
`/nosonda` - Toggle notifiche

`/usa forno` - Forno
`/noforno` - Toggle notifiche

📊 *Statistiche*
`/utilizzi` - Mostra quante volte hai usato ogni comando
`/siutilizzi` - Attiva notifiche giornaliere statistiche
`/noutilizzi` - Disattiva notifiche giornaliere statistiche

⚙️ *Preferenze*
`/impostazioni` - Gestisci le tue impostazioni

🔍 *Utilità*
`/start` - Avvia il bot e registrati per le notifiche
`/timer` - Controlla i tuoi timer attivi 
`/info` - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    # Use post_init for startup notifications
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # Registrazione dei handler per avventura
    app.add_handler(MessageHandler(filters.Regex(r'^/avventura(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_avventura_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/noavventura(?:@InventoryBot)?$'), toggle_avventura))
    
    # Registrazione degli handler per slot
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+(?:sl|slo|slot)(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_slot_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/noslot(?:@InventoryBot)?$'), toggle_slot))
    
    # Registrazione degli handler per borsellino
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+(?:borsellino|borse|bors|sell|sellino)(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_borsellino_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/noborsellino(?:@InventoryBot)?$'), toggle_borsellino))
    
    # Registrazione degli handler per nanoc
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+nanoc(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_nanoc_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/nonanoc(?:@InventoryBot)?$'), toggle_nanoc))
    
    # Registrazione degli handler per nanor
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+nanor(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_nanor_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/nonanor(?:@InventoryBot)?$'), toggle_nanor))
    
    # Registrazione degli handler per gica
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+gica(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_gica_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/nogica(?:@InventoryBot)?$'), toggle_gica))
    
    # Registrazione degli handler per pozzo
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+pozzo(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_pozzo_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/nopozzo(?:@InventoryBot)?$'), toggle_pozzo))
    
    # Registrazione degli handler per sonda
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+sonda(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_sonda_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/nosonda(?:@InventoryBot)?$'), toggle_sonda))
    
    # Registrazione degli handler per forno
    app.add_handler(MessageHandler(filters.Regex(r'^/usa\s+forno(?:@InventoryBot)?(?:\s+\d+(?::\d+)+)?$'), handle_forno_mention))
    app.add_handler(MessageHandler(filters.Regex(r'^/noforno(?:@InventoryBot)?$'), toggle_forno))
    
    # Registrazione dei comandi utility
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("timer", timer_command))
    app.add_handler(CommandHandler("impostazioni", impostazioni_command))
    
    # Registrazione handler per le impostazioni
    register_impostazioni_handlers(app)
    
    # Registrazione dei comandi per le statistiche
    app.add_handler(CommandHandler("utilizzi", handle_utilizzi_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/siutilizzi(?:@InventoryBot)?$'), toggle_utilizzi_notifications))
    app.add_handler(MessageHandler(filters.Regex(r'^/noutilizzi(?:@InventoryBot)?$'), toggle_utilizzi_notifications))
    
    # Registrazione dei comandi admin
    register_admin_handlers(app)
    
    # Job Queue per statistiche giornaliere
    job_queue = app.job_queue
    now = datetime.datetime.now()
    midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
    seconds_until_midnight = (midnight - now).total_seconds()
    
    # Reset contatori giornalieri
    job_queue.run_daily(
        lambda ctx: reset_daily_stats(),
        time=datetime.time(0, 1),  # 00:01 per dare tempo al job delle statistiche di eseguire
    )
    
    # Statistiche globali
    job_queue.run_repeating(
        send_daily_stats,
        interval=24*60*60,
        first=seconds_until_midnight
    )
    
    # Statistiche personali
    job_queue.run_repeating(
        send_daily_personal_stats, 
        interval=24*60*60,
        first=seconds_until_midnight - 60  # 1 minuto prima delle statistiche globali
    )

    print("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()