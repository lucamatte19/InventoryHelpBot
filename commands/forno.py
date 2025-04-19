import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    forno_times, active_forno_tasks, disabled_forno, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

async def check_cooldown_forno(user_id: int) -> bool:
    now = time.time()
    last_time = forno_times.get(user_id, 0)
    return now - last_time >= COOLDOWNS["forno"]

async def handle_forno_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[Forno] Received: '{update.message.text}'")
    regex_pattern = r'^/usa\s+forno(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        print("[Forno] Regex did not match.")
        return

    time_str = match.group(1)
    user = update.effective_user
    username = user.username or f"utente_{user.id}"
    item_name = "Forno"
    max_cooldown_seconds = COOLDOWNS["forno"]

    if time_str:  # Modify existing timer
        print(f"[{item_name}] Modify request detected. Time string: {time_str}")
        
        if user.id not in active_forno_tasks:
            await update.message.reply_text(
                f"@{username}, non c'è un forno attivo da modificare. Inizia prima con `/usa forno`."
            )
            print(f"[{item_name}] Modify failed: No active task for user {user.id}")
            return
            
        try:
            total_seconds = parse_dhms_time(time_str)
            if not total_seconds:
                await update.message.reply_text(
                    f"@{username}, formato ora non valido. Usa dd:hh:mm:ss."
                )
                return

            print(f"[{item_name}] Parsed modify time: {time_str} = {total_seconds}s")

            if total_seconds <= 0 or total_seconds > max_cooldown_seconds:
                max_time_str = format_remaining_time(max_cooldown_seconds)
                await update.message.reply_text(
                    f"@{username}, puoi modificare il timer solo con un tempo valido tra 00:00:00:01 e {max_time_str}!"
                )
                return

            await cancel_active_task(user.id, active_forno_tasks, item_name)

            await update.message.reply_text(
                f"@{username}, timer forno modificato! Ti avviserò appena pronto."
            )
            if user.id not in disabled_forno:
                new_task = asyncio.create_task(notifica_ritorno_forno_ridotto(update, user.id, username, total_seconds))
                active_forno_tasks[user.id] = new_task
                print(f"[{item_name}] Scheduled MODIFIED reduced notification task for user {user.id}")

        except ValueError:
            await update.message.reply_text(f"@{username}, formato ora non valido per la modifica. Usa dd:hh:mm:ss.")
            return
        except Exception as e:
             print(f"[{item_name}] Error during modification processing for user {user.id}: {e}")
             await update.message.reply_text(f"@{username}, si è verificato un errore durante la modifica del timer.")

    else:  # Start new timer
        print(f"[{item_name}] Start request detected.")
        
        if not await check_cooldown_forno(user.id):
            now = time.time()
            last_start_time = forno_times.get(user.id, 0)
            if last_start_time > 0:
                elapsed_time = now - last_start_time
                remaining_seconds = max(0, int(max_cooldown_seconds - elapsed_time))
                remaining_time_str = format_remaining_time(remaining_seconds)
                await update.message.reply_text(
                    f"@{username}, forno in cooldown! Prossimo forno disponibile tra: {remaining_time_str}"
                )
            else:
                await update.message.reply_text(f"@{username}, forno in cooldown!")

            print(f"[{item_name}] Start failed: User {user.id} on cooldown.")
            return

        await cancel_active_task(user.id, active_forno_tasks, item_name)

        forno_times[user.id] = time.time()
        daily_stats["forno"] += 1
        daily_stats["unique_users"].add(user.id)
        
        # Aggiorna statistiche personali dell'utente nel sistema persistente
        from utils.player_data import update_player_stats, update_last_timer, get_notification_status
        update_player_stats(user.id, "forno")
        update_last_timer(user.id, "forno", time.time())
        
        # Aggiorna statistiche in memoria (retrocompatibilità)
        if user.id not in user_stats:
            user_stats[user.id] = {}
        if "forno" not in user_stats[user.id]:
            user_stats[user.id]["forno"] = {"today": 0, "total": 0}
        user_stats[user.id]["forno"]["today"] = user_stats[user.id]["forno"].get("today", 0) + 1
        user_stats[user.id]["forno"]["total"] = user_stats[user.id]["forno"].get("total", 0) + 1

        # Verifica se l'utente vuole ricevere notifiche
        notifications_enabled = get_notification_status(user.id, "forno")
        
        # Se le notifiche sono disattivate, non rispondere affatto
        if user.id in disabled_forno or not notifications_enabled:
            print(f"[{item_name}] Notifications disabled for user {user.id}, not responding or scheduling task")
            return
        
        # Altrimenti, rispondi normalmente e pianifica task
        time_unit = format_remaining_time(max_cooldown_seconds)
        print(f"[{item_name}] Starting standard {time_unit} timer.")
        
        await update.message.reply_text(
            f"{user.mention_html()}, forno utilizzato! Ti avviserò appena pronto.",
            parse_mode="HTML"
        )
        task = asyncio.create_task(notifica_ritorno_forno(update, user.id, username))
        active_forno_tasks[user.id] = task
        print(f"[{item_name}] Scheduled standard notification task for user {user.id}")

async def notifica_ritorno_forno(update: Update, user_id: int, username: str):
    sleep_duration = COOLDOWNS["forno"]
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[Forno Default Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[Forno Default Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[Forno Default Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_forno_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[Forno Default Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return

    try:
        print(f"[Forno Default Task {task_id}] User {user_id}: Sending notification.")
        message = f"@{username}, puoi usare di nuovo il forno!\n/usa forno"
        await send_notification(update, user_id, username, message, "Forno")
    except Exception as e:
        print(f"[Forno Default Task {task_id}] Error sending notification for user {user_id}: {e}")
    finally:
        if user_id in active_forno_tasks and asyncio.current_task() == active_forno_tasks.get(user_id):
             print(f"[Forno Default Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_forno_tasks.pop(user_id, None)

async def notifica_ritorno_forno_ridotto(update: Update, user_id: int, username: str, total_seconds: int):
    sleep_duration = total_seconds
    item_name = "Forno"
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_forno_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return
        
    try:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sending notification.")
        past_time = time.time() - COOLDOWNS["forno"] - 1  # -1 per sicurezza
        forno_times[user_id] = past_time
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Updated timestamp to allow immediate restart.")
        
        message = f"@{username}, puoi usare di nuovo il forno!\n/usa forno"
        await send_notification(update, user_id, username, message, "Forno")
    except Exception as e:
        print(f"[{item_name} Reduced Task {task_id}] Error sending reduced notification for user {user_id}: {e}")
    finally:
        if user_id in active_forno_tasks and asyncio.current_task() == active_forno_tasks.get(user_id):
             print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_forno_tasks.pop(user_id, None)

async def toggle_forno(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user.id}"
    
    print(f"[Forno] Toggle command received for user {user_id} (@{username})")
    
    # Ottieni stato attuale dalle impostazioni salvate
    from utils.player_data import get_notification_status, update_player_notification_setting
    
    notifications_enabled = get_notification_status(user_id, "forno")
    print(f"[Forno] Current notification status: {'enabled' if notifications_enabled else 'disabled'}")
    
    # Aggiorna stato notifiche (manteniamo anche il vecchio sistema per retrocompatibilità)
    if notifications_enabled:
        disabled_forno.add(user_id)
        update_player_notification_setting(user_id, "forno", False)
        await update.message.reply_text(
            f"@{username}, ho disattivato le notifiche per il forno."
        )
        print(f"[Forno] Notifications disabled for user {user_id}")
    else:
        if user_id in disabled_forno:
            disabled_forno.remove(user_id)
        update_player_notification_setting(user_id, "forno", True)
        await update.message.reply_text(
            f"@{username}, ho riattivato le notifiche per il forno."
        )
        print(f"[Forno] Notifications enabled for user {user_id}")
