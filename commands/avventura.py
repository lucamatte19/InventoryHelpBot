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

async def handle_avventura_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[Avventura] Received: '{update.message.text}'")
    regex_pattern = r'^/avventura(?:@InventoryBot)?(?:\s+(\d+:\d+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        print("[Avventura] Regex did not match.")
        return

    time_str = match.group(1)
    user = update.effective_user
    username = user.username or f"utente_{user.id}"
    item_name = "Avventura"
    max_cooldown_seconds = COOLDOWNS["avventura"]

    if time_str:  # Modify existing timer
        print(f"[{item_name}] Modify request detected. Time string: {time_str}")
        
        if user.id not in active_avventura_tasks:
            await update.message.reply_text(
                f"@{username}, non c'è un'avventura attiva da modificare. Inizia prima con `/avventura`."
            )
            print(f"[{item_name}] Modify failed: No active task for user {user.id}")
            return
            
        try:
            m_str, s_str = time_str.split(':')
            m, s = int(m_str), int(s_str)
            total_seconds = m * 60 + s
            print(f"[{item_name}] Parsed modify time: {m}m {s}s = {total_seconds}s")

            if total_seconds <= 0 or total_seconds > max_cooldown_seconds:
                max_time_str = format_remaining_time(max_cooldown_seconds)
                await update.message.reply_text(
                    f"@{username}, puoi modificare il timer solo con un tempo valido tra 00:01 e {max_time_str} (formato: /avventura mm:ss)!"
                )
                return

            await cancel_active_task(user.id, active_avventura_tasks, item_name)

            await update.message.reply_text(
                f"@{username}, timer avventura modificato! Ti avviserò appena pronto."
            )
            if user.id not in disabled_avventura:
                new_task = asyncio.create_task(notifica_ritorno_avventura_ridotto(update, user.id, username, m, s))
                active_avventura_tasks[user.id] = new_task
                print(f"[{item_name}] Scheduled MODIFIED reduced notification task for user {user.id}")

        except ValueError:
            await update.message.reply_text(f"@{username}, formato ora non valido per la modifica. Usa mm:ss.")
            return
        except Exception as e:
             print(f"[{item_name}] Error during modification processing for user {user.id}: {e}")
             await update.message.reply_text(f"@{username}, si è verificato un errore durante la modifica del timer.")

    else:  # Start new timer
        print(f"[{item_name}] Start request detected.")
        
        if not await check_cooldown_avventura(user.id):
            now = time.time()
            last_start_time = avventura_times.get(user.id, 0)
            if last_start_time > 0:
                elapsed_time = now - last_start_time
                remaining_seconds = max(0, int(max_cooldown_seconds - elapsed_time))
                remaining_time_str = format_remaining_time(remaining_seconds)
                await update.message.reply_text(
                    f"@{username}, sei ancora in avventura! Prossima avventura disponibile tra circa: {remaining_time_str}"
                )
            else:
                 await update.message.reply_text(f"@{username}, sei ancora in avventura!")

            print(f"[{item_name}] Start failed: User {user.id} on cooldown.")
            return

        await cancel_active_task(user.id, active_avventura_tasks, item_name)

        avventura_times[user.id] = time.time()
        daily_stats["avventura"] += 1
        daily_stats["unique_users"].add(user.id)
        
        # Aggiorna statistiche personali dell'utente nel sistema persistente
        from utils.player_data import update_player_stats, update_last_timer
        update_player_stats(user.id, "avventura")
        update_last_timer(user.id, "avventura", time.time())
        
        # Aggiorna statistiche in memoria (retrocompatibilità)
        if user.id not in user_stats:
            user_stats[user.id] = {}
        if "avventura" not in user_stats[user.id]:
            user_stats[user.id]["avventura"] = {"today": 0, "total": 0}
        user_stats[user.id]["avventura"]["today"] = user_stats[user.id]["avventura"].get("today", 0) + 1

        time_unit = format_remaining_time(max_cooldown_seconds)
        print(f"[{item_name}] Starting standard {time_unit} adventure.")
        
        # Verifica se l'utente vuole ricevere notifiche (controlla sia in memoria che nel file)
        from utils.player_data import get_notification_status
        notifications_enabled = get_notification_status(user.id, "avventura")  # Modificato: user.id invece di user_id
        
        # Modifica il messaggio in base al fatto che le notifiche siano attive o meno
        if user.id not in disabled_avventura and notifications_enabled:
            await update.message.reply_text(
                f"{user.mention_html()}, avventura iniziata! Ti avviserò appena pronto.",
                parse_mode="HTML"
            )
            task = asyncio.create_task(notifica_ritorno_avventura(update, user.id, username))
            active_avventura_tasks[user.id] = task
            print(f"[{item_name}] Scheduled standard notification task for user {user.id}")
        else:
            await update.message.reply_text(
                f"{user.mention_html()}, avventura iniziata!",
                parse_mode="HTML"
            )
            print(f"[{item_name}] Notifications disabled for user {user.id}, not scheduling task")

async def notifica_ritorno_avventura(update: Update, user_id: int, username: str):
    sleep_duration = COOLDOWNS["avventura"]
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[Avventura Default Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[Avventura Default Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[Avventura Default Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_avventura_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[Avventura Default Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return

    try:
        print(f"[Avventura Default Task {task_id}] User {user_id}: Sending notification.")
        message = f"@{username}, puoi tornare ad avventurare!\n/avventura@InventoryBot"
        await send_notification(update, user_id, username, message, "Avventura")
    except Exception as e:
        print(f"[Avventura Default Task {task_id}] Error sending notification for user {user_id}: {e}")
    finally:
        if user_id in active_avventura_tasks and asyncio.current_task() == active_avventura_tasks.get(user_id):
             print(f"[Avventura Default Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_avventura_tasks.pop(user_id, None)

async def notifica_ritorno_avventura_ridotto(update: Update, user_id: int, username: str, m: int, s: int):
    sleep_duration = m * 60 + s
    item_name = "Avventura"
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({m}m {s}s).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_avventura_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return
        
    try:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sending notification.")
        past_time = time.time() - COOLDOWNS["avventura"] - 1  # -1 per sicurezza
        avventura_times[user_id] = past_time
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Updated timestamp to allow immediate restart.")
        
        message = f"@{username}, puoi tornare ad avventurare!\n/avventura@InventoryBot"
        await send_notification(update, user_id, username, message, "Avventura")
    except Exception as e:
        print(f"[{item_name} Reduced Task {task_id}] Error sending reduced notification for user {user_id}: {e}")
    finally:
        if user_id in active_avventura_tasks and asyncio.current_task() == active_avventura_tasks.get(user_id):
             print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_avventura_tasks.pop(user_id, None)

async def toggle_avventura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user.id}"
    
    print(f"[Avventura] Toggle command received for user {user_id} (@{username})")
    
    # Ottieni stato attuale dalle impostazioni salvate
    from utils.player_data import get_notification_status, update_player_notification_setting
    
    notifications_enabled = get_notification_status(user_id, "avventura")
    print(f"[Avventura] Current notification status: {'enabled' if notifications_enabled else 'disabled'}")
    
    # Aggiorna stato notifiche (manteniamo anche il vecchio sistema per retrocompatibilità)
    if notifications_enabled:
        disabled_avventura.add(user_id)
        update_player_notification_setting(user_id, "avventura", False)
        await update.message.reply_text(
            f"@{username}, ho disattivato le notifiche per l'avventura."
        )
        print(f"[Avventura] Notifications disabled for user {user_id}")
    else:
        if user_id in disabled_avventura:
            disabled_avventura.remove(user_id)
        update_player_notification_setting(user_id, "avventura", True)
        await update.message.reply_text(
            f"@{username}, ho riattivato le notifiche per l'avventura."
        )
        print(f"[Avventura] Notifications enabled for user {user_id}")
