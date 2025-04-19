import os
import json
import time
from typing import Dict, Any, Set

# Path per le statistiche globali
STATS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'global_stats.json')
ADMIN_PREFS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'admin_preferences.json')

def ensure_data_directory():
    """Assicura che la directory data esista."""
    data_dir = os.path.dirname(STATS_FILE_PATH)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def load_global_stats() -> Dict[str, Any]:
    """Carica le statistiche globali dal file JSON."""
    ensure_data_directory()
    
    if not os.path.exists(STATS_FILE_PATH):
        return {
            "total": {
                "avventura": 0,
                "slot": 0, 
                "borsellino": 0,
                "nanoc": 0,
                "nanor": 0,
                "gica": 0,
                "pozzo": 0,
                "sonda": 0,
                "forno": 0,
                "unique_users": 0
            },
            "daily": {
                "avventura": 0,
                "slot": 0, 
                "borsellino": 0,
                "nanoc": 0,
                "nanor": 0,
                "gica": 0,
                "pozzo": 0,
                "sonda": 0,
                "forno": 0,
                "unique_users": 0
            },
            "last_reset": int(time.time())
        }
    
    try:
        with open(STATS_FILE_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Errore nel caricamento delle statistiche globali: {e}")
        return {
            "total": {
                "avventura": 0,
                "slot": 0, 
                "borsellino": 0,
                "nanoc": 0,
                "nanor": 0,
                "gica": 0,
                "pozzo": 0,
                "sonda": 0,
                "forno": 0,
                "unique_users": 0
            },
            "daily": {
                "avventura": 0,
                "slot": 0, 
                "borsellino": 0,
                "nanoc": 0,
                "nanor": 0,
                "gica": 0,
                "pozzo": 0,
                "sonda": 0,
                "forno": 0,
                "unique_users": 0
            },
            "last_reset": int(time.time())
        }

def save_global_stats(stats: Dict[str, Any]) -> bool:
    """Salva le statistiche globali nel file JSON."""
    ensure_data_directory()
    
    try:
        # Converti i set in liste per la serializzazione JSON
        if "unique_users" in stats["daily"] and isinstance(stats["daily"]["unique_users"], set):
            stats["daily"]["unique_users"] = len(stats["daily"]["unique_users"])
        
        with open(STATS_FILE_PATH, 'w') as file:
            json.dump(stats, file, indent=2)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio delle statistiche globali: {e}")
        return False

def update_global_stats(daily_stats):
    """Aggiorna le statistiche globali con i dati correnti."""
    stats = load_global_stats()
    
    # Aggiorna le statistiche giornaliere
    stats["daily"] = {
        "avventura": daily_stats["avventura"],
        "slot": daily_stats["slot"],
        "borsellino": daily_stats["borsellino"],
        "nanoc": daily_stats["nanoc"],
        "nanor": daily_stats["nanor"],
        "gica": daily_stats["gica"],
        "pozzo": daily_stats["pozzo"],
        "sonda": daily_stats["sonda"],
        "forno": daily_stats["forno"],
        "unique_users": len(daily_stats["unique_users"])
    }
    
    # Aggiorna le statistiche totali
    for key in stats["daily"]:
        if key == "unique_users":
            continue  # Questo è un caso speciale, non sommiamo direttamente
        stats["total"][key] += daily_stats[key]
    
    # Aggiorna il timestamp dell'ultimo aggiornamento
    stats["last_reset"] = int(time.time())
    
    save_global_stats(stats)
    return stats

def get_admin_preferences() -> Dict[str, Any]:
    """Carica le preferenze dell'admin dal file JSON."""
    ensure_data_directory()
    
    if not os.path.exists(ADMIN_PREFS_FILE_PATH):
        # Impostazioni predefinite
        prefs = {"receive_daily_stats": True}
        save_admin_preferences(prefs)
        return prefs
    
    try:
        with open(ADMIN_PREFS_FILE_PATH, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Errore nel caricamento delle preferenze admin: {e}")
        return {"receive_daily_stats": True}  # Default a True in caso di errore

def save_admin_preferences(prefs: Dict[str, Any]) -> bool:
    """Salva le preferenze dell'admin nel file JSON."""
    ensure_data_directory()
    
    try:
        with open(ADMIN_PREFS_FILE_PATH, 'w') as file:
            json.dump(prefs, file, indent=2)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio delle preferenze admin: {e}")
        return False

def toggle_admin_stats_notification() -> bool:
    """Attiva/disattiva le notifiche statistiche per l'admin."""
    prefs = get_admin_preferences()
    prefs["receive_daily_stats"] = not prefs.get("receive_daily_stats", True)
    save_admin_preferences(prefs)
    return prefs["receive_daily_stats"]

def should_send_admin_stats() -> bool:
    """Verifica se l'admin dovrebbe ricevere le statistiche giornaliere."""
    prefs = get_admin_preferences()
    return prefs.get("receive_daily_stats", True)
