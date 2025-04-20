from telegram import Update
from telegram.ext import ContextTypes

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
✨ **InventoryHelpBot** ✨

⚙️ *Funzionamento Generale*
• I comandi avviano un timer standard
• Per modificare un timer attivo, aggiungi il tempo:
  • Formato breve: `/comando mm:ss` (minuti:secondi)
  • Formato esteso: `/comando hh:mm:ss` (ore:minuti:secondi)
  • Per settimanali: `/comando dd:hh:mm:ss` (giorni:ore:min:sec)
• Disattiva le notifiche con `/nocomando`

⏱️ *Comandi Disponibili*

🗡 *Avventura* (cooldown: 15 min)
`/avventura` - Avvia avventura
`/noavventura` - Toggle notifiche

💰 *Speciali*
`/usa slot` - Slot machine (cooldown: 5 min)
`/noslot` - Toggle notifiche

`/usa borsellino` - Borsellino (cooldown: 30 min)
`/noborsellino` - Toggle notifiche

📅 *Oggetti Giornalieri* (cooldown: 24 ore)
`/usa nanoc` - Impianto nanoreplicante 
`/nonanoc` - Toggle notifiche

`/usa nanor` - Nanoreplicante
`/nonanor` - Toggle notifiche

`/usa gica` - Piantina magica
`/nogica` - Toggle notifiche

`/usa pozzo` - Pozzo
`/nopozzo` - Toggle notifiche

`/usa compattatore` - Compattatore (cooldown: 24 ore)
`/nocompattatore` - Toggle notifiche

📆 *Oggetti Settimanali* (cooldown: 7 giorni)
`/usa sonda` - Sonda
`/nosonda` - Toggle notifiche

`/usa forno` - Forno
`/noforno` - Toggle notifiche

📊 *Statistiche*
`/utilizzi` - Mostra quante volte hai usato ogni comando
`/siutilizzi` - Attiva notifiche giornaliere statistiche
`/noutilizzi` - Disattiva notifiche giornaliere statistiche

⚙️ *Preferenze*
`/impostazioni` - Gestisci le tue impostazioni e scegli dove ricevere le notifiche

🔍 *Utilità*
`/start` - Avvia il bot e registrati per le notifiche
`/timer` - Controlla i tuoi timer attivi 
`/info` - Mostra questo messaggio
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")
