import asyncio
import re
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.timer_data import (
    nanor_times, active_nanor_tasks, disabled_nanor, 
    COOLDOWNS, daily_stats, TIMER_DATA, user_stats  # Aggiunto user_stats
)
from utils.messaging import send_notification

async def check_cooldown_nanor(user_id: int) -> bool:
    now = time.time()
    last_time = nanor_times.get(user_id, 0)
    return now - last_time >= COOLDOWNS["nanor"]

async def handle_nanor_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[NanoR] Received: '{update.message.text}'")
    regex_pattern = r'^/usa\s+nanor(?:@InventoryBot)?(?:\s+(\d+(?::\d+)+))?$'
    match = re.match(regex_pattern, update.message.text)

    if not match:
        print("[NanoR] Regex did not match.")
        return

    time_str = match.group(1)
    user = update.effective_user
    username = user.username or f"utente_{user.id}"
    item_name = "Nanoreplicante"
    max_cooldown_seconds = COOLDOWNS["nanor"]

    if time_str:  # Modify existing timer
        print(f"[{item_name}] Modify request detected. Time string: {time_str}")
        
        if user.id not in active_nanor_tasks:
            await update.message.reply_text(
                f"@{username}, non c'è un nanoreplicante attivo da modificare. Inizia prima con `/usa nanor`."
            )
            print(f"[{item_name}] Modify failed: No active task for user {user.id}")
            return
            
        try:
            total_seconds = parse_dhms_time(time_str)
            if not total_seconds:
                await update.message.reply_text(
                    f"@{username}, formato ora non valido. Usa hh:mm:ss."
                )
                return

            print(f"[{item_name}] Parsed modify time: {time_str} = {total_seconds}s")

            if total_seconds <= 0 or total_seconds > max_cooldown_seconds:
                max_time_str = format_remaining_time(max_cooldown_seconds)
                await update.message.reply_text(
                    f"@{username}, puoi modificare il timer solo con un tempo valido tra 00:00:01 e {max_time_str}!"
                )
                return

            await cancel_active_task(user.id, active_nanor_tasks, item_name)

            await update.message.reply_text(
                f"@{username}, timer nanoreplicante modificato! Ti avviserò tra {format_remaining_time(total_seconds)}."
            )
            if user.id not in disabled_nanor:
                new_task = asyncio.create_task(notifica_ritorno_nanor_ridotto(update, user.id, username, total_seconds))
                active_nanor_tasks[user.id] = new_task
                print(f"[{item_name}] Scheduled MODIFIED reduced notification task for user {user.id}")

        except ValueError:
            await update.message.reply_text(f"@{username}, formato ora non valido per la modifica. Usa hh:mm:ss.")
            return
        except Exception as e:
             print(f"[{item_name}] Error during modification processing for user {user.id}: {e}")
             await update.message.reply_text(f"@{username}, si è verificato un errore durante la modifica del timer.")

    else:  # Start new timer
        print(f"[{item_name}] Start request detected.")
        
        if not await check_cooldown_nanor(user.id):
            now = time.time()
            last_start_time = nanor_times.get(user.id, 0)
            if last_start_time > 0:
                elapsed_time = now - last_start_time
                remaining_seconds = max(0, int(max_cooldown_seconds - elapsed_time))
                remaining_time_str = format_remaining_time(remaining_seconds)
                await update.message.reply_text(
                    f"@{username}, nanoreplicante in cooldown! Prossimo nanoreplicante disponibile tra: {remaining_time_str}"
                )
            else:
                await update.message.reply_text(f"@{username}, nanoreplicante in cooldown!")

            print(f"[{item_name}] Start failed: User {user.id} on cooldown.")
            return

        await cancel_active_task(user.id, active_nanor_tasks, item_name)

        nanor_times[user.id] = time.time()
        daily_stats["nanor"] += 1
        daily_stats["unique_users"].add(user.id)
        
        # Aggiorna statistiche personali dell'utente nel sistema persistente
        from utils.player_data import update_player_stats, update_last_timer, get_notification_status
        update_player_stats(user.id, "nanor")
        update_last_timer(user.id, "nanor", time.time())
        
        # Aggiorna statistiche in memoria (retrocompatibilità)
        if user.id not in user_stats:
            user_stats[user.id] = {}
        if "nanor" not in user_stats[user.id]:
            user_stats[user.id]["nanor"] = {"today": 0, "total": 0}
        user_stats[user.id]["nanor"]["today"] = user_stats[user.id]["nanor"].get("today", 0) + 1
        user_stats[user.id]["nanor"]["total"] = user_stats[user.id]["nanor"].get("total", 0) + 1

        # Verifica se l'utente vuole ricevere notifiche
        notifications_enabled = get_notification_status(user.id, "nanor")
        
        # Se le notifiche sono disattivate, non rispondere affatto
        if user.id in disabled_nanor or not notifications_enabled:
            print(f"[{item_name}] Notifications disabled for user {user.id}, not responding or scheduling task")
            return
        
        # Altrimenti, rispondi normalmente e pianifica task
        time_unit = format_remaining_time(max_cooldown_seconds)
        print(f"[{item_name}] Starting standard {time_unit} timer.")
        
        await update.message.reply_text(
            f"{user.mention_html()}, nanoreplicante utilizzato! Ti avviserò tra {time_unit}.",
            parse_mode="HTML"
        )
        if user.id not in disabled_nanor:
            task = asyncio.create_task(notifica_ritorno_nanor(update, user.id, username))
            active_nanor_tasks[user.id] = task
            print(f"[{item_name}] Scheduled standard notification task for user {user.id}")

async def notifica_ritorno_nanor(update: Update, user_id: int, username: str):
    sleep_duration = COOLDOWNS["nanor"]
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[NanoR Default Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[NanoR Default Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[NanoR Default Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_nanor_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[NanoR Default Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return

    try:
        print(f"[NanoR Default Task {task_id}] User {user_id}: Sending notification.")
        message = f"@{username}, puoi usare di nuovo il nanoreplicante!\n/usa nanor"
        await send_notification(update, user_id, username, message, "NanoR")
    except Exception as e:
        print(f"[NanoR Default Task {task_id}] Error sending notification for user {user_id}: {e}")
    finally:
        if user_id in active_nanor_tasks and asyncio.current_task() == active_nanor_tasks.get(user_id):
             print(f"[NanoR Default Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_nanor_tasks.pop(user_id, None)

async def notifica_ritorno_nanor_ridotto(update: Update, user_id: int, username: str, total_seconds: int):
    sleep_duration = total_seconds
    item_name = "Nanoreplicante"
    task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
    try:
        await asyncio.sleep(sleep_duration)
    except asyncio.CancelledError:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task cancelled during sleep.")
        raise

    print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
    
    current_active_task = active_nanor_tasks.get(user_id)
    if not current_active_task or current_active_task != asyncio.current_task():
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
        return
        
    try:
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Sending notification.")
        past_time = time.time() - COOLDOWNS["nanor"] - 1  # -1 per sicurezza
        nanor_times[user_id] = past_time
        print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Updated timestamp to allow immediate restart.")
        
        message = f"@{username}, puoi usare di nuovo il nanoreplicante!\n/usa nanor"
        await send_notification(update, user_id, username, message, "NanoR")
    except Exception as e:
        print(f"[{item_name} Reduced Task {task_id}] Error sending reduced notification for user {user_id}: {e}")
    finally:
        if user_id in active_nanor_tasks and asyncio.current_task() == active_nanor_tasks.get(user_id):
             print(f"[{item_name} Reduced Task {task_id}] User {user_id}: Cleaning up active task entry.")
             active_nanor_tasks.pop(user_id, None)

async def toggle_nanor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or f"utente_{user.id}"
    
    print(f"[Nanor] Toggle command received for user {user_id} (@{username})")
    
    # Ottieni stato attuale dalle impostazioni salvate
    from utils.player_data import get_notification_status, update_player_notification_setting
    
    notifications_enabled = get_notification_status(user_id, "nanor")
    print(f"[Nanor] Current notification status: {'enabled' if notifications_enabled else 'disabled'}")
    
    # Aggiorna stato notifiche (manteniamo anche il vecchio sistema per retrocompatibilità)
    if notifications_enabled:
        disabled_nanor.add(user_id)
        update_player_notification_setting(user_id, "nanor", False)
        await update.message.reply_text(
            f"@{username}, ho disattivato le notifiche per il nanoreplicante."
        )
        print(f"[Nanor] Notifications disabled for user {user_id}")
    else:
        if user_id in disabled_nanor:
            disabled_nanor.remove(user_id)
        update_player_notification_setting(user_id, "nanor", True)
        await update.message.reply_text(
            f"@{username}, ho riattivato le notifiche per il nanoreplicante."
        )
        print(f"[Nanor] Notifications enabled for user {user_id}")
