import os
import json
import time
import asyncio  # Aggiunto import asyncio
from pathlib import Path

# Crea la cartella players se non esiste
players_dir = Path("/home/pi/Desktop/InventoryHelpBot/players")
players_dir.mkdir(exist_ok=True)

# Struttura di default per i dati del giocatore
DEFAULT_PLAYER_DATA = {
    "settings": {
        "notifications": {
            "avventura": True,
            "slot": True,
            "borsellino": True,
            "nanoc": True,
            "nanor": True,
            "gica": True,
            "pozzo": True,
            "sonda": True,
            "forno": True,
            "compattatore": True  # Aggiunto compattatore
        },
        "startup_notifications": False,  # Cambiato da True a False
        "daily_stats": False
    },
    "stats": {
        "avventura": {"today": 0, "total": 0},
        "slot": {"today": 0, "total": 0},
        "borsellino": {"today": 0, "total": 0},
        "nanoc": {"today": 0, "total": 0},
        "nanor": {"today": 0, "total": 0},
        "gica": {"today": 0, "total": 0},
        "pozzo": {"today": 0, "total": 0},
        "sonda": {"today": 0, "total": 0},
        "forno": {"today": 0, "total": 0},
        "compattatore": {"today": 0, "total": 0}  # Aggiunto compattatore
    },
    "last_timers": {
        "avventura": 0,
        "slot": 0,
        "borsellino": 0,
        "nanoc": 0,
        "nanor": 0,
        "gica": 0,
        "pozzo": 0,
        "sonda": 0,
        "forno": 0,
        "compattatore": 0  # Aggiunto compattatore
    },
    "username": "",
    "register_date": 0,
    "last_active": 0
}

# Cache dei dati dei giocatori in memoria
player_cache = {}

def get_player_file_path(user_id):
    """Restituisce il percorso del file per un utente specifico."""
    return players_dir / f"{user_id}.json"

def load_player_data(user_id):
    """Carica i dati di un giocatore dal file o crea un nuovo profilo."""
    if user_id in player_cache:
        return player_cache[user_id]
        
    file_path = get_player_file_path(user_id)
    
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Assicurati che i dati hanno tutti i campi necessari
                for key, value in DEFAULT_PLAYER_DATA.items():
                    if key not in data:
                        data[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in data[key]:
                                data[key][subkey] = subvalue
                            elif isinstance(subvalue, dict) and isinstance(data[key][subkey], dict):
                                for sub_subkey, sub_subvalue in subvalue.items():
                                    if sub_subkey not in data[key][subkey]:
                                        data[key][subkey][sub_subkey] = sub_subvalue
                
                player_cache[user_id] = data
                return data
        except Exception as e:
            print(f"Errore nel caricamento dei dati per l'utente {user_id}: {e}")
    
    # Se il file non esiste o c'è stato un errore, crea un nuovo profilo
    player_cache[user_id] = DEFAULT_PLAYER_DATA.copy()
    player_cache[user_id]["register_date"] = int(time.time())
    player_cache[user_id]["last_active"] = int(time.time())
    save_player_data(user_id)
    
    return player_cache[user_id]

def save_player_data(user_id):
    """Salva i dati di un giocatore nel file."""
    if user_id not in player_cache:
        return False
    
    file_path = get_player_file_path(user_id)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(player_cache[user_id], f, indent=2)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio dei dati per l'utente {user_id}: {e}")
        return False

def update_player_notification_setting(user_id, command, enabled):
    """Aggiorna le impostazioni di notifica di un giocatore per un comando specifico."""
    data = load_player_data(user_id)
    data["settings"]["notifications"][command] = enabled
    data["last_active"] = int(time.time())
    return save_player_data(user_id)

def update_player_stats(user_id, command_name):
    """Aggiorna le statistiche di utilizzo di un comando per un utente."""
    try:
        data = load_player_data(user_id)
        
        # Assicurati che esistano le strutture necessarie
        if "stats" not in data:
            data["stats"] = {}
        if command_name not in data["stats"]:
            data["stats"][command_name] = {"today": 0, "total": 0}
        
        # Incrementa i contatori giornaliero e totale
        data["stats"][command_name]["today"] = data["stats"][command_name].get("today", 0) + 1
        data["stats"][command_name]["total"] = data["stats"][command_name].get("total", 0) + 1
        
        save_player_data(user_id, data)
        return True
    except Exception as e:
        print(f"Errore nell'aggiornamento delle statistiche per l'utente {user_id}: {e}")
        return False

def update_username(user_id, username):
    """Aggiorna l'username del giocatore."""
    data = load_player_data(user_id)
    if username and username != f"utente_{user_id}":  # Aggiorna solo se l'username è valido
        data["username"] = username
    data["last_active"] = int(time.time())
    return save_player_data(user_id)

def update_daily_stats_subscription(user_id, subscribed):
    """Aggiorna l'iscrizione alle statistiche giornaliere."""
    data = load_player_data(user_id)
    data["settings"]["daily_stats"] = subscribed
    data["last_active"] = int(time.time())
    return save_player_data(user_id)

def update_startup_notification_setting(user_id, enabled):
    """Aggiorna le impostazioni di notifica all'avvio del bot."""
    data = load_player_data(user_id)
    data["settings"]["startup_notifications"] = enabled
    data["last_active"] = int(time.time())
    return save_player_data(user_id)

def update_last_timer(user_id, command, timestamp):
    """Aggiorna il timestamp dell'ultimo utilizzo di un timer."""
    data = load_player_data(user_id)
    data["last_timers"][command] = timestamp
    data["last_active"] = int(time.time())
    return save_player_data(user_id)

def reset_daily_stats():
    """Resetta le statistiche giornaliere e aggiorna i totali."""
    print("Resetting daily stats...")
    
    # Prima di resettare, salva le statistiche giornaliere nel file persistente
    from utils.stats_manager import update_global_stats
    from utils.timer_data import daily_stats
    
    # Aggiorna il file delle statistiche globali
    update_global_stats(daily_stats)
    
    # Ora resetta le statistiche giornaliere
    for key in daily_stats:
        if key == "unique_users":
            daily_stats[key] = set()
        else:
            daily_stats[key] = 0
    
    # Resetta anche i contatori giornalieri nei dati utente
    for user_id in daily_stats_subscribers:
        data = load_player_data(user_id)
        if "stats" in data:
            for cmd in data["stats"]:
                if "today" in data["stats"][cmd]:
                    data["stats"][cmd]["today"] = 0
            save_player_data(user_id, data)

def get_all_subscribes_users():
    """Ottiene tutti gli utenti iscritti alle statistiche giornaliere."""
    subscribed_users = []
    
    # Controlla prima la cache
    for user_id, data in player_cache.items():
        if data["settings"].get("daily_stats", False):
            subscribed_users.append(user_id)
    
    # Poi controlla i file per gli utenti non in cache
    for file in players_dir.glob("*.json"):
        try:
            user_id = int(file.stem)
            if user_id not in player_cache:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "settings" in data and "daily_stats" in data["settings"] and data["settings"]["daily_stats"]:
                        subscribed_users.append(user_id)
        except Exception as e:
            print(f"Errore nella lettura delle impostazioni per {file}: {e}")
    
    return subscribed_users

def get_notification_status(user_id, command):
    """Verifica se le notifiche sono attive per un comando specifico."""
    data = load_player_data(user_id)
    return data["settings"]["notifications"].get(command, True)  # Default a True se non specificato

def get_startup_notification_status(user_id):
    """Verifica se le notifiche di avvio sono attive per un utente."""
    data = load_player_data(user_id)
    return data["settings"].get("startup_notifications", False)  # Cambiato da True a False

async def recreate_active_timers():
    """Ricrea i task di notifica per i timer che erano attivi prima del riavvio."""
    print("Ricreazione task di notifica per timer attivi...")
    
    from utils.timer_data import TIMER_DATA, TOKEN
    from utils.messaging import send_direct_message
    
    now = time.time()
    recreated_tasks = 0
    
    for command_name, data in TIMER_DATA.items():
        times_dict = data["times"]
        active_tasks_dict = data["active"]
        max_cooldown = data["cooldown"]
        
        for user_id, timestamp in times_dict.items():
            # Calcola quanto tempo è passato dall'avvio del timer
            elapsed = now - timestamp
            
            # Se il timer è ancora attivo (non è passato tutto il cooldown)
            if 0 < elapsed < max_cooldown:
                # Calcola quanto tempo manca alla fine del cooldown
                remaining_seconds = max_cooldown - elapsed
                
                # Verifica se l'utente ha le notifiche attive
                from utils.player_data import get_notification_status
                notifications_enabled = get_notification_status(user_id, command_name)
                
                disabled_set = data["disabled"]
                if user_id not in disabled_set and notifications_enabled:
                    # Crea un nuovo task per la notifica
                    print(f"[{command_name}] Ricreando task di notifica per utente {user_id}, tempo rimanente: {remaining_seconds:.2f}s")
                    
                    # Ottieni l'username se possibile
                    try:
                        from telegram.ext import ApplicationBuilder
                        temp_app = ApplicationBuilder().token(TOKEN).build()
                        chat = await temp_app.bot.get_chat(user_id)
                        username = chat.username or f"utente_{user_id}"
                    except:
                        username = f"utente_{user_id}"
                    
                    async def notify_after_restart(user_id, username, command, remaining):
                        try:
                            await asyncio.sleep(remaining)
                            message = ""
                            if command == "avventura":
                                message = f"@{username}, puoi tornare ad avventurare!\n/avventura@InventoryBot"
                            else:
                                message = f"@{username}, puoi usare di nuovo {command}!\n/usa {command}"
                                
                            await send_direct_message(user_id, message, command.capitalize())
                            
                            # Rimuovi il task attivo dopo averlo completato
                            if user_id in TIMER_DATA[command]["active"]:
                                TIMER_DATA[command]["active"].pop(user_id, None)
                        except asyncio.CancelledError:
                            print(f"[{command.capitalize()}] Task riavviato cancellato per utente {user_id}")
                    
                    # Crea e registra il nuovo task
                    task = asyncio.create_task(notify_after_restart(user_id, username, command_name, remaining_seconds))
                    active_tasks_dict[user_id] = task
                    recreated_tasks += 1
    
    print(f"Ricreati {recreated_tasks} task di notifica per timer attivi.")
    return recreated_tasks

def sync_timers_from_files():
    """Sincronizza i timer dalle informazioni nei file JSON."""
    print("Sincronizzazione timer dai file JSON...")
    updated_timers = 0
    
    from utils.timer_data import TIMER_DATA, registered_users
    
    # Itera attraverso tutti gli utenti registrati
    for user_id in registered_users:
        try:
            data = load_player_data(user_id)
            last_timers = data.get("last_timers", {})
            
            # Itera attraverso tutti i tipi di timer
            for command, timestamp in last_timers.items():
                if command in TIMER_DATA and timestamp > 0:
                    # Aggiorna il timestamp in memoria
                    TIMER_DATA[command]["times"][user_id] = timestamp
                    updated_timers += 1
            
        except Exception as e:
            print(f"Errore nella sincronizzazione timer per l'utente {user_id}: {e}")
    
    print(f"Sincronizzati {updated_timers} timer.")
    return updated_timers

async def migrate_existing_data(registered_users, disabled_commands, user_stats, timer_data):
    """Migra i dati esistenti al nuovo sistema di file."""
    print("Iniziando migrazione dei dati esistenti...")
    
    try:
        # Migra utenti registrati
        for user_id in registered_users:
            data = load_player_data(user_id)
            data["last_active"] = int(time.time())
            save_player_data(user_id)
        
        # Migra impostazioni di notifica disattivate E sincronizza le impostazioni da persistente a memoria
        for cmd_name, disabled_set in disabled_commands.items():
            # Primo passaggio: salva lo stato in memoria nel sistema persistente
            for user_id in disabled_set:
                if user_id:  # Verifica che l'ID utente sia valido
                    update_player_notification_setting(user_id, cmd_name, False)
            
            # Secondo passaggio: sincronizza da persistente alla memoria per assicurare coerenza
            for user_id in registered_users:
                if user_id:  # Verifica che l'ID utente sia valido
                    notifications_enabled = get_notification_status(user_id, cmd_name)
                    if not notifications_enabled and user_id not in disabled_set:
                        print(f"Sincronizzando impostazioni per {user_id}, disattivando notifiche {cmd_name}")
                        disabled_set.add(user_id)
                    elif notifications_enabled and user_id in disabled_set:
                        print(f"Sincronizzando impostazioni per {user_id}, attivando notifiche {cmd_name}")
                        disabled_set.remove(user_id)
        
        # Migra statistiche di utilizzo
        for user_id, stats in user_stats.items():
            if user_id:  # Verifica che l'ID utente sia valido
                data = load_player_data(user_id)
                for cmd_name, cmd_stats in stats.items():
                    if cmd_name in data["stats"]:
                        data["stats"][cmd_name].update(cmd_stats)
                save_player_data(user_id)
        
        # Migra timestamp dei timer
        for cmd_name, cmd_data in timer_data.items():
            times_dict = cmd_data.get("times", {})
            for user_id, timestamp in times_dict.items():
                if user_id:  # Verifica che l'ID utente sia valido
                    update_last_timer(user_id, cmd_name, timestamp)
        
        # Sincronizza i timer dai file JSON alle strutture in memoria
        sync_timers_from_files()
        
        # Ricrea i task di notifica per i timer attivi
        await recreate_active_timers()
        
        print("Migrazione dati completata con successo!")
        return True
    except Exception as e:
        print(f"Errore durante la migrazione dei dati: {e}")
        return False

def ensure_complete_data_structure(data):
    """Assicura che i dati utente abbiano tutte le sezioni necessarie."""
    if "settings" not in data:
        data["settings"] = {}
    
    if "notifications" not in data["settings"]:
        data["settings"]["notifications"] = {}
    
    # Assicurati che ci siano tutti i comandi incluso compattatore
    for cmd in ["avventura", "slot", "borsellino", "nanoc", "nanor", 
               "gica", "pozzo", "sonda", "forno", "compattatore"]:
        if cmd not in data["settings"]["notifications"]:
            data["settings"]["notifications"][cmd] = True
    
    if "stats" not in data:
        data["stats"] = {}
    
    # Assicurati che ci siano tutte le statistiche
    for cmd in ["avventura", "slot", "borsellino", "nanoc", "nanor", 
               "gica", "pozzo", "sonda", "forno", "compattatore"]:
        if cmd not in data["stats"]:
            data["stats"][cmd] = {"today": 0, "total": 0}
    
    if "last_timers" not in data:
        data["last_timers"] = {}
    
    # Assicurati che ci siano tutti i timer
    for cmd in ["avventura", "slot", "borsellino", "nanoc", "nanor", 
               "gica", "pozzo", "sonda", "forno", "compattatore"]:
        if cmd not in data["last_timers"]:
            data["last_timers"][cmd] = 0

def create_default_player_data():
    """Crea una struttura dati di default per un nuovo utente."""
    return {
        "settings": {
            "notifications": {
                "avventura": True,
                "slot": True,
                "borsellino": True,
                "nanoc": True,
                "nanor": True,
                "gica": True,
                "pozzo": True,
                "sonda": True,
                "forno": True,
                "compattatore": True  # Aggiunto compattatore
            },
            "daily_stats": False,
            "startup_notifications": True
        },
        "stats": {
            "avventura": {"today": 0, "total": 0},
            "slot": {"today": 0, "total": 0},
            "borsellino": {"today": 0, "total": 0},
            "nanoc": {"today": 0, "total": 0},
            "nanor": {"today": 0, "total": 0},
            "gica": {"today": 0, "total": 0},
            "pozzo": {"today": 0, "total": 0},
            "sonda": {"today": 0, "total": 0},
            "forno": {"today": 0, "total": 0},
            "compattatore": {"today": 0, "total": 0}  # Aggiunto compattatore
        },
        "last_timers": {
            "avventura": 0,
            "slot": 0,
            "borsellino": 0,
            "nanoc": 0,
            "nanor": 0,
            "gica": 0,
            "pozzo": 0,
            "sonda": 0,
            "forno": 0,
            "compattatore": 0  # Aggiunto compattatore
        },
        "username": "",
        "register_date": int(time.time()),
        "last_active": int(time.time())
    }
