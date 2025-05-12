import discord
from discord import app_commands
from discord.ext import commands
from utils.sheet_utils import save_log_to_google_sheets, remove_log_from_google_sheets, get_logs_ws, get_log_channel_id
from utils.decorators import check_permissions, check_public_permissions

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Commande pour définir le salon de logs
    @check_permissions("set_logs")
    @app_commands.command(name="set_logs", description="Définir le salon de logs pour ce serveur.")
    @app_commands.describe(salon="Le salon dans lequel les logs seront envoyés.")
    async def set_logs(self, interaction: discord.Interaction, salon: discord.TextChannel):
        """Permet à l'utilisateur de définir un salon de logs."""
        guild_id = str(interaction.guild.id)  # Le guild_id doit être converti en chaîne
        # Réponse différée pour éviter le timeout
        await interaction.response.defer(ephemeral=True)

        # Vérification si le salon est valide
        if salon not in interaction.guild.text_channels:
            await interaction.followup.send("Ce salon n'existe pas ou n'est pas un salon texte valide.", ephemeral=True)
            return

        # Sauvegarder le salon choisi dans Google Sheets
        save_log_to_google_sheets(interaction.guild.id, salon.id)
        
        # Envoyer un message confirmant la définition du salon
        await interaction.followup.send(f"Salon de logs défini pour ce serveur : {salon.mention}", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a configuré le salon de logs sur {salon.mention}")

    # Commande pour supprimer le salon de logs
    @check_permissions("remove_logs")
    @app_commands.command(name="remove_logs", description="Supprimer le salon de logs pour ce serveur.")
    async def remove_logs(self, interaction: discord.Interaction):
        """Permet à l'utilisateur de supprimer le salon de logs."""
        guild_id = str(interaction.guild.id)
        await interaction.response.defer(ephemeral=True)

        # Supprimer le salon de logs de Google Sheets
        remove_log_from_google_sheets(guild_id)
        
        # Envoyer un message confirmant la suppression
        await interaction.followup.send("Salon de logs supprimé pour ce serveur.", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a supprimé la configuration du salon de logs")


# Fonction asynchrone pour envoyer le message dans le salon de logs
async def send_log_message(interaction, message):
    try:
        log_channel_id = get_log_channel_id(str(interaction.guild.id))
        if log_channel_id:
            log_channel = interaction.guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(message)
            else:
                print(f"Salon de logs introuvable : {log_channel_id}")
        else:
            print(f"Aucun salon de logs configuré pour {interaction.guild.id}")
    except Exception as e:
        print(f"Erreur lors de l'envoi du log : {e}")

async def setup(bot):
    await bot.add_cog(Logs(bot))