import asyncio
from utils.player_data import update_last_timer

async def cancel_active_task(user_id: int, active_tasks_dict: dict, item_name: str):
    """Cancella e rimuove un task attivo se esiste."""
    if user_id in active_tasks_dict:
        try:
            print(f"[{item_name}] Cancelling active task for user {user_id}.")
            active_tasks_dict[user_id].cancel()
        except Exception as e:
            print(f"[{item_name}] Error cancelling task for user {user_id}: {e}")
        finally:
            # Rimuovi l'entry indipendentemente dal successo della cancellazione
            if user_id in active_tasks_dict:
                del active_tasks_dict[user_id]
