import os
import logging
import traceback
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Creazione della cartella per i log se non esiste
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
ERROR_LOG_DIR = os.path.join(LOG_DIR, 'errors')

# Crea le cartelle se non esistono
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ERROR_LOG_DIR, exist_ok=True)

# Configura il logger principale
def setup_logger():
    logger = logging.getLogger('InventoryHelpBot')
    logger.setLevel(logging.INFO)
    
    # Formato del log: timestamp, livello, messaggio
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler per log info
    info_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'bot.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    
    # Handler specifico per gli errori
    error_handler = RotatingFileHandler(
        os.path.join(ERROR_LOG_DIR, 'errors.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Handler per la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Aggiungi gli handler al logger
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger principale
logger = setup_logger()

def log_error(error, context=None):
    """
    Registra un errore completo con traceback e contesto.
    
    Args:
        error: L'eccezione da registrare
        context: Informazioni aggiuntive sul contesto dell'errore
    """
    error_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Crea un file separato per ogni errore con timestamp
    error_file = os.path.join(ERROR_LOG_DIR, f"error_{error_time}.log")
    
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"=== Errore registrato alle {error_time} ===\n\n")
        
        if context:
            f.write(f"Contesto: {context}\n\n")
        
        f.write(f"Tipo di errore: {type(error).__name__}\n")
        f.write(f"Messaggio: {str(error)}\n\n")
        f.write("Traceback:\n")
        f.write(traceback.format_exc())
    
    # Registra anche nel log principale
    logger.error(f"Errore: {type(error).__name__} - {str(error)}")
    logger.error(f"Dettagli salvati in: {error_file}")
    
    return error_file
