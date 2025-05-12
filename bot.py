### === Réorganisation du projet en Cogs ===

# Structure du dossier :
# .
# ├── bot.py (démarrage du bot)
# ├── cogs/
# │   ├── embed.py
# │            ├──/embed
# │   ├── permissions.py
# │            ├──/set_perms
# │            ├──/remove_perms
# │            ├──/see_perms
# │   ├── login.py
# │            ├──/set_login
# │            ├──/login
# │            ├──/remove_login_config
# │   ├── logs.py
# │            ├──/set_logs
# │            ├──/remove_logs
# │   ├── moderations.py
# │            ├──/ban
# │            ├──/ban_list
# │            ├──/unban
# │            ├──/kick
# │            ├──/mute
# │            ├──/unmute
# │            ├──/clear
# │            ├──/slowmode
# │            ├──/serverinfo
# │   └── make_serv.py
# │            ├──/make_serv
# │            ├──/reset_serv
# │   ├── community.py
# │            ├──/sondage
# │            ├──/suggestion
# │            ├──/say
# │            ├──/avis
# │   ├── absences.py
# │            ├──/absent
# │            ├──/absence_config
# │            ├──/absence_stop
# │            ├──/absence_list
# │            ├──/absence_info
# │   ├── members.py
# │            ├──/set_join_message
# │            ├──/set_leave_message
# │   ├── help.py
# │            ├──/ping
# │            ├──/support
# ├── utils/
# │   ├── sheet_utils.py
# │   ├── guild_check.py
# │   └── decorators.py
# ├── keep_alive.py
# ├── credentials.json
# └── .env

# =============================

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from dotenv import load_dotenv
import os
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Chargement des Cogs
initial_extensions = [
    "cogs.embed",
    "cogs.logs", 
    "cogs.login",
    "cogs.permissions",
    "cogs.moderations",
    "cogs.make_serv",
    "cogs.community",
    "cogs.absences",
    "cogs.members",
    "cogs.help",
    "cogs.fun",
]

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        # Répond directement dans Discord de façon propre
        if not interaction.response.is_done():
            await interaction.response.send_message("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
        else:
            await interaction.followup.send("🚫 Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f"✅ Connecté en tant que {bot.user}.")
    
    # Charger les cogs en premier
    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"🔌 Cog chargée : {ext}")
        except Exception as e:
            logger.error(f"❌ Erreur de chargement pour {ext} : {e}")

    # Synchronisation des commandes slash après avoir chargé les cogs
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔁 Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        logger.error(f"⚠️ Erreur de synchronisation des commandes slash : {e}")

@bot.event
async def on_message(message):
    # Permet de ne pas bloquer les commandes avec des messages non commandés
    if message.author == bot.user:
        return
    await bot.process_commands(message)

# Lancer le serveur Flask dans un thread
if __name__ == "__main__":
    from threading import Thread
    from keep_alive import run
    Thread(target=run).start()  # Lancer le serveur Flask
    bot.run(token)  # Lancer le bot Discord

