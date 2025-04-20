import asyncio
import time
from telegram import Update
from telegram.ext import ContextTypes

from utils.formatters import format_remaining_time, parse_dhms_time
from utils.helpers import cancel_active_task
from utils.messaging import send_notification
from utils.player_data import update_player_stats, update_last_timer, get_notification_status, update_player_notification_setting, get_preferred_notification_chat
from utils.timer_data import daily_stats, user_stats, TIMER_DATA
from utils.logger import logger

class TimerHandler:
    """Classe generica per gestire i timer dei vari comandi."""
    
    def __init__(self, command_name):
        """Inizializza un handler di timer per un comando specifico.
        
        Args:
            command_name: Nome del comando (es. 'avventura', 'nanoc', 'compattatore')
        """
        self.command_name = command_name
        self.data = TIMER_DATA[command_name]
        self.times_dict = self.data["times"]
        self.active_tasks = self.data["active"]
        self.disabled_set = self.data["disabled"]
        self.cooldown = self.data["cooldown"]
        self.emoji = self.data["emoji"]
        
        # Nome visualizzato (prima lettera maiuscola)
        self.display_name = command_name.capitalize()
    
    async def check_cooldown(self, user_id):
        """Verifica se il cooldown è scaduto per un utente."""
        now = time.time()
        last_time = self.times_dict.get(user_id, 0)
        return now - last_time >= self.cooldown
    
    async def handle_command(self, update, context, regex_match):
        """Gestisce l'esecuzione del comando."""
        time_str = regex_match.group(1) if regex_match else None
        user = update.effective_user
        user_id = user.id
        username = user.username or f"utente_{user_id}"
        
        logger.info(f"[{self.display_name}] Processing command for user {user_id} ({username})")
        
        if time_str:
            await self._handle_timer_modification(update, user_id, username, time_str)
        else:
            await self._handle_new_timer(update, user_id, username)
    
    async def _handle_timer_modification(self, update, user_id, username, time_str):
        """Gestisce la modifica di un timer esistente."""
        logger.info(f"[{self.display_name}] Modify request detected. Time string: {time_str}")
        
        if user_id not in self.active_tasks:
            await update.message.reply_text(
                f"@{username}, non c'è un {self.command_name} attivo da modificare. " +
                f"Inizia prima con `/usa {self.command_name}`."
            )
            logger.info(f"[{self.display_name}] Modify failed: No active task for user {user_id}")
            return
            
        try:
            total_seconds = parse_dhms_time(time_str)
            if not total_seconds:
                await update.message.reply_text(
                    f"@{username}, formato ora non valido. Usa il formato appropriato."
                )
                return

            logger.info(f"[{self.display_name}] Parsed modify time: {time_str} = {total_seconds}s")

            if total_seconds <= 0 or total_seconds > self.cooldown:
                max_time_str = format_remaining_time(self.cooldown)
                await update.message.reply_text(
                    f"@{username}, puoi modificare il timer solo con un tempo valido tra 00:00:01 e {max_time_str}!"
                )
                return

            await cancel_active_task(user_id, self.active_tasks, self.display_name)

            await update.message.reply_text(
                f"@{username}, timer {self.command_name} modificato! Ti avviserò appena pronto."
            )
            if user_id not in self.disabled_set:
                new_task = asyncio.create_task(
                    self._notify_after_custom_duration(update, user_id, username, total_seconds)
                )
                self.active_tasks[user_id] = new_task
                logger.info(f"[{self.display_name}] Scheduled MODIFIED reduced notification task for user {user_id}")

        except ValueError:
            await update.message.reply_text(f"@{username}, formato ora non valido per la modifica.")
            return
        except Exception as e:
             logger.error(f"[{self.display_name}] Error during modification processing for user {user_id}: {e}")
             await update.message.reply_text(f"@{username}, si è verificato un errore durante la modifica del timer.")
    
    async def _handle_new_timer(self, update, user_id, username):
        """Gestisce l'avvio di un nuovo timer."""
        logger.info(f"[{self.display_name}] Start request detected.")
        
        if not await self.check_cooldown(user_id):
            now = time.time()
            last_start_time = self.times_dict.get(user_id, 0)
            if last_start_time > 0:
                elapsed_time = now - last_start_time
                remaining_seconds = max(0, int(self.cooldown - elapsed_time))
                remaining_time_str = format_remaining_time(remaining_seconds)
                await update.message.reply_text(
                    f"@{username}, {self.command_name} in cooldown! Prossimo {self.command_name} disponibile tra: {remaining_time_str}"
                )
            else:
                await update.message.reply_text(f"@{username}, {self.command_name} in cooldown!")

            logger.info(f"[{self.display_name}] Start failed: User {user_id} on cooldown.")
            return

        await cancel_active_task(user_id, self.active_tasks, self.display_name)

        self.times_dict[user_id] = time.time()
        daily_stats[self.command_name] += 1
        daily_stats["unique_users"].add(user_id)
        
        # Aggiorna statistiche personali dell'utente nel sistema persistente
        update_player_stats(user_id, self.command_name)
        update_last_timer(user_id, self.command_name, time.time())
        
        # Aggiorna statistiche in memoria (retrocompatibilità)
        if user_id not in user_stats:
            user_stats[user_id] = {}
        if self.command_name not in user_stats[user_id]:
            user_stats[user_id][self.command_name] = {"today": 0, "total": 0}
        user_stats[user_id][self.command_name]["today"] = user_stats[user_id][self.command_name].get("today", 0) + 1
        user_stats[user_id][self.command_name]["total"] = user_stats[user_id][self.command_name].get("total", 0) + 1

        # Verifica se l'utente vuole ricevere notifiche
        notifications_enabled = get_notification_status(user_id, self.command_name)
        
        # Se le notifiche sono disattivate, non rispondere affatto
        if user_id in self.disabled_set or not notifications_enabled:
            logger.info(f"[{self.display_name}] Notifications disabled for user {user_id}, not responding or scheduling task")
            return
        
        # Altrimenti, rispondi normalmente e pianifica task
        time_unit = format_remaining_time(self.cooldown)
        logger.info(f"[{self.display_name}] Starting standard {time_unit} timer.")
        
        await update.message.reply_text(
            f"{update.effective_user.mention_html()}, {self.command_name} utilizzato! Ti avviserò appena pronto.",
            parse_mode="HTML"
        )
        task = asyncio.create_task(self._notify_after_default_duration(update, user_id, username))
        self.active_tasks[user_id] = task
        logger.info(f"[{self.display_name}] Scheduled standard notification task for user {user_id}")
    
    async def _notify_after_default_duration(self, update, user_id, username):
        """Invia una notifica dopo la durata standard del cooldown."""
        sleep_duration = self.cooldown
        task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
        logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
        try:
            await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Task cancelled during sleep.")
            raise

        logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
        
        current_active_task = self.active_tasks.get(user_id)
        if not current_active_task or current_active_task != asyncio.current_task():
            logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
            return

        try:
            logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Sending notification.")
            
            # Personalizza il messaggio in base al comando
            if self.command_name == "avventura":
                message = f"@{username}, puoi tornare ad avventurare!\n/avventura@InventoryBot"
            else:
                message = f"@{username}, puoi usare di nuovo {self.command_name}!\n/usa {self.command_name}"
                
            await send_notification(update, user_id, username, message, self.display_name)
        except Exception as e:
            logger.error(f"[{self.display_name} Default Task {task_id}] Error sending notification for user {user_id}: {e}")
        finally:
            if user_id in self.active_tasks and asyncio.current_task() == self.active_tasks.get(user_id):
                logger.info(f"[{self.display_name} Default Task {task_id}] User {user_id}: Cleaning up active task entry.")
                self.active_tasks.pop(user_id, None)

    async def _notify_after_custom_duration(self, update, user_id, username, total_seconds):
        """Invia una notifica dopo una durata personalizzata."""
        sleep_duration = total_seconds
        task_id = asyncio.current_task().get_name() if hasattr(asyncio.current_task(), 'get_name') else id(asyncio.current_task())
        logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Sleeping for {sleep_duration} seconds ({format_remaining_time(sleep_duration)}).")
        try:
            await asyncio.sleep(sleep_duration)
        except asyncio.CancelledError:
            logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Task cancelled during sleep.")
            raise

        logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Woke up after {sleep_duration} seconds.")
        
        current_active_task = self.active_tasks.get(user_id)
        if not current_active_task or current_active_task != asyncio.current_task():
            logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Task is no longer active or has been replaced. Exiting.")
            return
            
        try:
            logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Sending notification.")
            past_time = time.time() - self.cooldown - 1  # -1 per sicurezza
            self.times_dict[user_id] = past_time
            logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Updated timestamp to allow immediate restart.")
            
            # Personalizza il messaggio in base al comando
            if self.command_name == "avventura":
                message = f"@{username}, puoi tornare ad avventurare!\n/avventura@InventoryBot"
            else:
                message = f"@{username}, puoi usare di nuovo {self.command_name}!\n/usa {self.command_name}"
                
            await send_notification(update, user_id, username, message, self.display_name)
        except Exception as e:
            logger.error(f"[{self.display_name} Reduced Task {task_id}] Error sending reduced notification for user {user_id}: {e}")
        finally:
            if user_id in self.active_tasks and asyncio.current_task() == self.active_tasks.get(user_id):
                logger.info(f"[{self.display_name} Reduced Task {task_id}] User {user_id}: Cleaning up active task entry.")
                self.active_tasks.pop(user_id, None)
    
    async def toggle_notifications(self, update, context):
        """Attiva/disattiva le notifiche per questo comando."""
        user = update.effective_user
        user_id = user.id
        username = user.username or f"utente_{user_id}"
        
        logger.info(f"[{self.display_name}] Toggle command received for user {user_id} (@{username})")
        
        # Ottieni stato attuale dalle impostazioni salvate
        notifications_enabled = get_notification_status(user_id, self.command_name)
        logger.info(f"[{self.display_name}] Current notification status: {'enabled' if notifications_enabled else 'disabled'}")
        
        # Aggiorna stato notifiche (manteniamo anche il vecchio sistema per retrocompatibilità)
        if notifications_enabled:
            self.disabled_set.add(user_id)
            update_player_notification_setting(user_id, self.command_name, False)
            await update.message.reply_text(
                f"@{username}, ho disattivato le notifiche per {self.command_name}."
            )
            logger.info(f"[{self.display_name}] Notifications disabled for user {user_id}")
        else:
            if user_id in self.disabled_set:
                self.disabled_set.remove(user_id)
            update_player_notification_setting(user_id, self.command_name, True)
            await update.message.reply_text(
                f"@{username}, ho riattivato le notifiche per {self.command_name}."
            )
            logger.info(f"[{self.display_name}] Notifications enabled for user {user_id}")
