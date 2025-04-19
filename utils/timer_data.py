import time
import configparser
import os

# Leggi il token dal file di configurazione
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
config.read(config_path)

# Ottieni il token
TOKEN = config.get('bot', 'token', fallback=None)
if not TOKEN:
    raise ValueError("TOKEN non trovato nel file config.ini. Assicurati che esista una sezione [bot] con un'opzione 'token'.")

# --- Cooldown Durations (in seconds) ---
try:
    COOLDOWNS = {
        "avventura": config.getint('timers', 'avventura', fallback=15) * 60,
        "slot": config.getint('timers', 'slot', fallback=5) * 60,
        "borsellino": config.getint('timers', 'borsellino', fallback=30) * 60,
        "nanoc": config.getint('timers', 'nanoc', fallback=24) * 3600,
        "nanor": config.getint('timers', 'nanor', fallback=24) * 3600,
        "gica": config.getint('timers', 'gica', fallback=24) * 3600,
        "pozzo": config.getint('timers', 'pozzo', fallback=24) * 3600,
        "sonda": config.getint('timers', 'sonda', fallback=168) * 3600,
        "forno": config.getint('timers', 'forno', fallback=168) * 3600,
    }
except (configparser.NoSectionError, configparser.NoOptionError, ValueError) as e:
    print(f"Warning: Error reading cooldowns from config.ini ({e}). Using defaults.")
    COOLDOWNS = {
        "avventura": 15 * 60, "slot": 5 * 60, "borsellino": 30 * 60,
        "nanoc": 24 * 3600, "nanor": 24 * 3600, "gica": 24 * 3600,
        "pozzo": 24 * 3600, "sonda": 7 * 24 * 3600, "forno": 7 * 24 * 3600,
    }

# --- Emojis ---
EMOJIS = {
    "avventura": "🗡", "slot": "🎰", "borsellino": "💰",
    "nanoc": "🧪", "nanor": "🔄", "gica": "🧙‍♂️",
    "pozzo": "🚰", "sonda": "🔍", "forno": "🔥",
}

# Statistiche giornaliere
daily_stats = {
    "avventura": 0,
    "slot": 0,
    "borsellino": 0, 
    "nanoc": 0,
    "nanor": 0,
    "gica": 0,
    "pozzo": 0,
    "sonda": 0,
    "forno": 0,
    "unique_users": set()  # Set per utenti unici
}

# Strutture per tracciare le statistiche individuali di utilizzo per ogni utente
# Formato: {user_id: {command: {"today": count, "total": count}}}
user_stats = {}

# Set per gli utenti che vogliono ricevere statistiche giornaliere
daily_stats_subscribers = set()

ADMIN_USERNAME = "LucaQuelloFigo"  # L'username che riceverà le statistiche

# Dictionaries to track timer data
avventura_times = {}  # Struttura: {user_id: timestamp}
slot_times = {}
borsellino_times = {}
nanoc_times = {}
nanor_times = {}
gica_times = {}
pozzo_times = {}
sonda_times = {}
forno_times = {}

# Set per memorizzare quali utenti hanno disattivato le notifiche
disabled_avventura = set()
disabled_slot = set()
disabled_borsellino = set()
disabled_nanoc = set()
disabled_nanor = set()
disabled_gica = set()
disabled_pozzo = set()
disabled_sonda = set()
disabled_forno = set()

# Dizionari per tenere traccia dei task attivi per ogni comando
active_avventura_tasks = {}  # {user_id: task}
active_slot_tasks = {}
active_borsellino_tasks = {}
active_nanoc_tasks = {}
active_nanor_tasks = {}
active_gica_tasks = {}
active_pozzo_tasks = {}
active_sonda_tasks = {}
active_forno_tasks = {}

# Set per memorizzare gli utenti che hanno avviato il bot
registered_users = set()

# Funzione per salvare gli utenti registrati al bot in config.ini
def save_registered_users():
    # Converti il set in una stringa con gli ID separati da virgole
    users_str = ','.join([str(user_id) for user_id in registered_users])
    
    # Assicurati che esista la sezione 'users'
    if 'users' not in config:
        config['users'] = {}
    
    config['users']['registered_ids'] = users_str
    
    try:
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        print(f"Saved {len(registered_users)} registered users to config.")
    except Exception as e:
        print(f"Error saving registered users: {e}")

# Funzione per caricare gli utenti registrati da config.ini
def load_registered_users():
    try:
        if 'users' in config and 'registered_ids' in config['users']:
            users_str = config['users']['registered_ids']
            if users_str:
                ids = users_str.split(',')
                for id_str in ids:
                    try:
                        registered_users.add(int(id_str))
                    except ValueError:
                        print(f"Warning: Invalid user ID in config: {id_str}")
            print(f"Loaded {len(registered_users)} registered users from config.")
    except Exception as e:
        print(f"Error loading registered users: {e}")

# Carica gli utenti registrati all'avvio
load_registered_users()

# --- All Timer Data ---
# Combine times dicts, cooldowns, disabled sets, active tasks, etc. for easier iteration
TIMER_DATA = {
    "avventura": {"times": avventura_times, "disabled": disabled_avventura, "active": active_avventura_tasks, "cooldown": COOLDOWNS["avventura"], "emoji": EMOJIS["avventura"]},
    "slot": {"times": slot_times, "disabled": disabled_slot, "active": active_slot_tasks, "cooldown": COOLDOWNS["slot"], "emoji": EMOJIS["slot"]},
    "borsellino": {"times": borsellino_times, "disabled": disabled_borsellino, "active": active_borsellino_tasks, "cooldown": COOLDOWNS["borsellino"], "emoji": EMOJIS["borsellino"]},
    "nanoc": {"times": nanoc_times, "disabled": disabled_nanoc, "active": active_nanoc_tasks, "cooldown": COOLDOWNS["nanoc"], "emoji": EMOJIS["nanoc"]},
    "nanor": {"times": nanor_times, "disabled": disabled_nanor, "active": active_nanor_tasks, "cooldown": COOLDOWNS["nanor"], "emoji": EMOJIS["nanor"]},
    "gica": {"times": gica_times, "disabled": disabled_gica, "active": active_gica_tasks, "cooldown": COOLDOWNS["gica"], "emoji": EMOJIS["gica"]},
    "pozzo": {"times": pozzo_times, "disabled": disabled_pozzo, "active": active_pozzo_tasks, "cooldown": COOLDOWNS["pozzo"], "emoji": EMOJIS["pozzo"]},
    "sonda": {"times": sonda_times, "disabled": disabled_sonda, "active": active_sonda_tasks, "cooldown": COOLDOWNS["sonda"], "emoji": EMOJIS["sonda"]},
    "forno": {"times": forno_times, "disabled": disabled_forno, "active": active_forno_tasks, "cooldown": COOLDOWNS["forno"], "emoji": EMOJIS["forno"]},
}
