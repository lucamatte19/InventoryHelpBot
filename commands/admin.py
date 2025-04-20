import asyncio
import telegram  # Aggiunto import per gestire le eccezioni BadRequest
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
import datetime
import time

from utils.formatters import format_remaining_time
from utils.timer_data import (
    TIMER_DATA, user_stats, registered_users, ADMIN_USERNAME,
    daily_stats, daily_stats_subscribers, config, config_path
)
from utils.stats_manager import toggle_admin_stats_notification, should_send_admin_stats

async def is_admin(update: Update) -> bool:
    """Verifica se l'utente è un amministratore."""
    user = update.effective_user
    is_admin_user = user.username == ADMIN_USERNAME
    if not is_admin_user:
        await update.message.reply_text(
            "⛔ Questo comando è riservato all'amministratore."
        )
    return is_admin_user

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra le statistiche di utilizzo dei comandi (per admin)."""
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("⛔️ Questo comando è riservato all'amministratore.")
        return
    
    # Carica le statistiche globali dal file
    from utils.stats_manager import load_global_stats
    stats = load_global_stats()
    
    reply_text = "📊 *Statistiche Globali del Bot* 📊\n\n"
    
    # Statistiche giornaliere
    reply_text += "*Utilizzi Oggi:*\n"
    for cmd, count in daily_stats.items():
        if cmd != "unique_users":
            emoji = TIMER_DATA[cmd]["emoji"] if cmd in TIMER_DATA else "📈"
            reply_text += f"{emoji} {cmd.capitalize()}: {count}\n"
    reply_text += f"👥 Utenti unici oggi: {len(daily_stats['unique_users'])}\n\n"
    
    # Statistiche totali da file
    reply_text += "*Utilizzi Totali (persistenti):*\n"
    for cmd, count in stats["total"].items():
        if cmd != "unique_users":
            emoji = TIMER_DATA[cmd]["emoji"] if cmd in TIMER_DATA else "📈"
            # Escape eventuali caratteri speciali nel nome del comando
            safe_cmd = cmd.replace("*", "\\*").replace("_", "\\_").replace("`", "\\`").replace("[", "\\[")
            reply_text += f"{emoji} {safe_cmd.capitalize()}: {count}\n"
    
    # Stato impostazioni
    reply_text += "\n*Impostazioni Admin:*\n"
    status = "✅ Attivo" if should_send_admin_stats() else "❌ Disattivato"
    reply_text += f"📧 Ricezione stats giornaliere: {status}\n"
    reply_text += "Usa /toggle\\_stats per cambiare questa impostazione"
    
    try:
        await update.message.reply_text(reply_text, parse_mode="Markdown")
    except telegram.error.BadRequest as e:
        # In caso di errore, prova a inviare senza formattazione
        print(f"Errore nell'invio del messaggio formattato: {e}")
        plain_text = reply_text.replace('*', '').replace('_', '')
        await update.message.reply_text(f"⚠️ Errore di formattazione\n\n{plain_text}")

async def toggle_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva/disattiva le notifiche statistiche giornaliere per l'admin."""
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("⛔️ Questo comando è riservato all'amministratore.")
        return
    
    enabled = toggle_admin_stats_notification()
    status = "attivate ✅" if enabled else "disattivate ❌"
    await update.message.reply_text(f"📊 Notifiche statistiche giornaliere {status}")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elenca tutti gli utenti registrati."""
    if not await is_admin(update):
        return
    
    if not registered_users:
        await update.message.reply_text("Nessun utente registrato.")
        return
    
    response_lines = [f"👥 *Utenti Registrati ({len(registered_users)})*:"]
    
    # Raggruppiamo gli utenti in blocchi di 20 per evitare messaggi troppo lunghi
    user_blocks = [list(registered_users)[i:i+20] for i in range(0, len(registered_users), 20)]
    
    for i, block in enumerate(user_blocks):
        if i > 0:  # Se abbiamo più di un blocco, invia messaggi multipli
            msg = await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")
            response_lines = []  # Reset per il prossimo blocco
        
        for user_id in block:
            # Per ogni utente, aggiungi statistiche base
            user_commands = len([cmd for cmd in user_stats.get(user_id, {}) if user_stats[user_id][cmd].get("today", 0) > 0])
            in_daily_stats = "✅" if user_id in daily_stats_subscribers else "❌"
            response_lines.append(f"🆔 `{user_id}` - Comandi oggi: {user_commands} - Notifiche: {in_daily_stats}")
    
    # Invia l'ultimo blocco o l'unico blocco se ce n'è solo uno
    await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")

async def admin_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informazioni dettagliate su un utente specifico."""
    if not await is_admin(update):
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "Utilizzo: `/admin_user_info [user_id]`", 
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(args[0])
        if user_id not in registered_users:
            await update.message.reply_text(f"❌ Utente {user_id} non trovato tra gli utenti registrati.")
            return
        
        response_lines = [f"👤 *Informazioni Utente* `{user_id}`"]
        
        # Info base
        subscription_status = "✅ Attivo" if user_id in daily_stats_subscribers else "❌ Disattivo"
        response_lines.append(f"🔔 *Abbonamento notifiche*: {subscription_status}")
        
        # Statistiche utilizzo per ogni comando
        response_lines.append("\n📈 *Statistiche Utilizzo*:")
        if user_id in user_stats:
            for command, stats in user_stats[user_id].items():
                emoji = TIMER_DATA.get(command, {}).get("emoji", "📝")
                today_count = stats.get("today", 0)
                total_count = stats.get("total", 0)
                response_lines.append(f"{emoji} *{command.capitalize()}*: {today_count} oggi, {total_count} totali")
        else:
            response_lines.append("Nessuna statistica disponibile.")
        
        # Timer attivi
        response_lines.append("\n⏱️ *Timer Attivi*:")
        active_timers = []
        for command, data in TIMER_DATA.items():
            if user_id in data["active"]:
                emoji = data["emoji"]
                active_timers.append(f"{emoji} {command.capitalize()}")
        
        if active_timers:
            response_lines.extend(active_timers)
        else:
            response_lines.append("Nessun timer attivo.")
        
        # Timer in cooldown
        response_lines.append("\n⏳ *Timer in Cooldown*:")
        cooldown_timers = []
        now = time.time()
        
        for command, data in TIMER_DATA.items():
            times_dict = data["times"]
            max_cooldown = data["cooldown"]
            emoji = data["emoji"]
            
            if user_id in times_dict:
                last_time = times_dict[user_id]
                elapsed = now - last_time
                remaining = max(0, max_cooldown - elapsed)
                
                if remaining > 0:
                    remaining_str = format_remaining_time(int(remaining))
                    cooldown_timers.append(f"{emoji} {command.capitalize()}: {remaining_str}")
        
        if cooldown_timers:
            response_lines.extend(cooldown_timers)
        else:
            response_lines.append("Nessun timer in cooldown.")
        
        # Opzioni notifiche
        response_lines.append("\n🔕 *Notifiche Disattivate*:")
        disabled_notifications = []
        for command, data in TIMER_DATA.items():
            if user_id in data["disabled"]:
                emoji = data["emoji"]
                disabled_notifications.append(f"{emoji} {command.capitalize()}")
        
        if disabled_notifications:
            response_lines.extend(disabled_notifications)
        else:
            response_lines.append("Tutte le notifiche sono attive.")
        
        # Azioni admin possibili
        response_lines.append("\n⚙️ *Azioni Amministratore*:")
        response_lines.append(f"Per resettare un timer: `/admin_reset {user_id} [nome_comando]`")
        response_lines.append(f"Per inviare un messaggio: `/admin_message {user_id} [messaggio]`")
        
        await update.message.reply_text("\n".join(response_lines), parse_mode="Markdown")
        
    except ValueError:
        await update.message.reply_text("❌ ID utente non valido. Deve essere un numero intero.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def admin_reset_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resetta un timer specifico per un utente."""
    if not await is_admin(update):
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Utilizzo: `/admin_reset [user_id] [comando]`\n"
            "Comandi disponibili: avventura, slot, borsellino, nanoc, nanor, gica, pozzo, sonda, forno", 
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(args[0])
        command = args[1].lower()
        
        if command not in TIMER_DATA:
            await update.message.reply_text(f"❌ Comando '{command}' non valido.")
            return
        
        # Resetta il timer (imposta a un tempo passato per renderlo disponibile)
        past_time = time.time() - TIMER_DATA[command]["cooldown"] - 1
        TIMER_DATA[command]["times"][user_id] = past_time
        
        # Cancella anche eventuali task attivi
        if user_id in TIMER_DATA[command]["active"]:
            try:
                TIMER_DATA[command]["active"][user_id].cancel()
            except:
                pass
            del TIMER_DATA[command]["active"][user_id]
        
        await update.message.reply_text(
            f"✅ Timer '{command}' resettato per l'utente {user_id}. Il comando è ora disponibile."
        )
        
    except ValueError:
        await update.message.reply_text("❌ ID utente non valido. Deve essere un numero intero.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invia un messaggio a tutti gli utenti registrati."""
    if not await is_admin(update):
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "Utilizzo: `/admin_broadcast [messaggio]`", 
            parse_mode="Markdown"
        )
        return
    
    message = " ".join(args)
    
    # Crea un messaggio di conferma con un keyboard inline
    confirm_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Conferma", callback_data=f"broadcast_confirm_{update.effective_user.id}"),
            InlineKeyboardButton("❌ Annulla", callback_data=f"broadcast_cancel_{update.effective_user.id}")
        ]
    ])
    
    preview_message = f"📣 *ANTEPRIMA MESSAGGIO*\n\n{message}\n\n*Confermi l'invio a {len(registered_users)} utenti?*"
    
    # Salva il messaggio nel context.user_data per recuperarlo nel callback
    # NON creare un nuovo dizionario, aggiungi una chiave a quello esistente
    if context.user_data is not None:  # Verifica che user_data non sia None
        context.user_data["broadcast_message"] = message
    
    await update.message.reply_text(
        preview_message,
        reply_markup=confirm_keyboard,
        parse_mode="Markdown"
    )

async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce le callback dei bottoni per il broadcast."""
    query = update.callback_query
    await query.answer()
    
    # Estrai l'ID dell'admin e l'azione (confirm/cancel)
    parts = query.data.split("_")
    action = parts[1]
    admin_id = int(parts[2])
    
    # Verifica che l'utente che ha premuto il bottone sia lo stesso che ha richiesto il broadcast
    if update.effective_user.id != admin_id:
        await query.edit_message_text("❌ Non sei autorizzato a confermare questo messaggio.")
        return
    
    if action == "cancel":
        await query.edit_message_text("❌ Invio del messaggio annullato.")
        return
    
    # Procedi con l'invio del messaggio
    message = context.user_data.get("broadcast_message", "") if context.user_data else ""
    if not message:
        await query.edit_message_text("❌ Errore: messaggio non trovato.")
        return
    
    # Invia il messaggio a tutti gli utenti
    sent_count = 0
    error_count = 0
    
    await query.edit_message_text("⏳ Invio messaggio in corso...")
    
    for user_id in registered_users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📣 *MESSAGGIO DALL'AMMINISTRATORE*\n\n{message}",
                parse_mode="Markdown"
            )
            sent_count += 1
            # Breve pausa per evitare di raggiungere limiti di rate
            await asyncio.sleep(0.1)
        except Exception as e:
            error_count += 1
            print(f"Error sending broadcast to user {user_id}: {e}")
    
    summary = f"✅ Messaggio inviato a {sent_count} utenti.\n❌ Errori: {error_count}"
    await query.edit_message_text(summary)

async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Invia un messaggio a un utente specifico."""
    if not await is_admin(update):
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Utilizzo: `/admin_message [user_id] [messaggio]`", 
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id = int(args[0])
        message = " ".join(args[1:])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📣 *MESSAGGIO DALL'AMMINISTRATORE*\n\n{message}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(f"✅ Messaggio inviato con successo all'utente {user_id}.")
        
    except ValueError:
        await update.message.reply_text("❌ ID utente non valido. Deve essere un numero intero.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nell'invio del messaggio: {str(e)}")

async def admin_setstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Imposta statistiche per un utente o per tutti."""
    if not await is_admin(update):
        return
    
    args = context.args
    usage = (
        "Utilizzo: `/admin_setstats [user_id|all] [comando] [today|total] [valore]`\n"
        "Esempio: `/admin_setstats 123456789 slot today 5`\n"
        "Comandi disponibili: avventura, slot, borsellino, nanoc, nanor, gica, pozzo, sonda, forno"
    )
    
    if len(args) != 4:
        await update.message.reply_text(usage, parse_mode="Markdown")
        return
    
    target, command, stat_type, value = args
    
    # Verifica che il comando esista
    from utils.timer_data import TIMER_DATA
    if command not in TIMER_DATA:
        await update.message.reply_text(f"❌ Comando '{command}' non valido.", parse_mode="Markdown")
        return
    
    # Verifica che il tipo di statistica sia valido
    if stat_type not in ["today", "total"]:
        await update.message.reply_text(f"❌ Tipo di statistica '{stat_type}' non valido. Usa 'today' o 'total'.", parse_mode="Markdown")
        return
    
    # Verifica che il valore sia un intero valido
    try:
        value = int(value)
        if value < 0:
            await update.message.reply_text("❌ Il valore deve essere un numero intero positivo.", parse_mode="Markdown")
            return
    except ValueError:
        await update.message.reply_text("❌ Il valore deve essere un numero intero.", parse_mode="Markdown")
        return
    
    from utils.player_data import load_player_data, save_player_data
    
    if target == "all":
        # Aggiorna le statistiche per tutti gli utenti
        from utils.timer_data import registered_users
        updated_count = 0
        
        for user_id in registered_users:
            try:
                data = load_player_data(user_id)
                if command in data["stats"]:
                    data["stats"][command][stat_type] = value
                    save_player_data(user_id)
                    updated_count += 1
            except Exception as e:
                print(f"Error updating stats for user {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Aggiornate statistiche '{command}.{stat_type}' a {value} per {updated_count} utenti.", 
            parse_mode="Markdown"
        )
    else:
        # Aggiorna le statistiche per un utente specifico
        try:
            user_id = int(target)
            data = load_player_data(user_id)
            
            if command in data["stats"]:
                data["stats"][command][stat_type] = value
                save_player_data(user_id)
                
                await update.message.reply_text(
                    f"✅ Aggiornate statistiche '{command}.{stat_type}' a {value} per l'utente {user_id}.", 
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ Comando '{command}' non trovato nelle statistiche dell'utente {user_id}.", 
                    parse_mode="Markdown"
                )
        except ValueError:
            await update.message.reply_text("❌ ID utente non valido.", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Errore: {str(e)}", parse_mode="Markdown")

async def info_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra i comandi admin disponibili solo all'amministratore."""
    if not await is_admin(update):
        return
    
    admin_help_text = """
🔐 *Comandi Amministratore* 🔐

Ecco l'elenco dei comandi disponibili solo per te, amministratore:

📊 *Statistiche e Utenti*:
`/admin_stats` - Mostra statistiche globali del bot
`/admin_users` - Elenca tutti gli utenti registrati
`/admin_user_info [user_id]` - Mostra info dettagliate su un utente specifico
`/admin_setstats [user_id|all] [comando] [today|total] [valore]` - Imposta statistiche per un utente

⏱️ *Gestione Timer*:
`/admin_reset [user_id] [comando]` - Resetta un timer specifico

📣 *Comunicazioni*:
`/admin_broadcast [messaggio]` - Invia un messaggio a tutti gli utenti
`/admin_message [user_id] [messaggio]` - Invia un messaggio a un utente specifico

ℹ️ *Aiuto*:
`/info_admin` - Mostra questo messaggio

Ricorda che questi comandi non sono visibili agli utenti normali.
"""
    
    await update.message.reply_text(admin_help_text, parse_mode="Markdown")

# Funzione di registrazione degli handler
def register_admin_handlers(app):
    """Registra gli handler per i comandi admin."""
    from telegram.ext import CommandHandler
    
    app.add_handler(CommandHandler("admin_stats", admin_stats))
    app.add_handler(CommandHandler("toggle_stats", toggle_admin_stats))
    app.add_handler(CommandHandler("admin_users", admin_users))
    app.add_handler(CommandHandler("admin_user_info", admin_user_info))
    app.add_handler(CommandHandler("admin_reset", admin_reset_timer))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    app.add_handler(CommandHandler("admin_message", admin_message))
    app.add_handler(CommandHandler("admin_setstats", admin_setstats))
    app.add_handler(CommandHandler("info_admin", info_admin_command))
    
    # Handler per la callback del broadcast
    app.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern=r'^broadcast_'))
