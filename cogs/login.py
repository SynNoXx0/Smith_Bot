import discord
from discord import app_commands
from discord.ext import commands
from utils.sheet_utils import get_login_ws, get_logs_ws
from utils.decorators import check_permissions, check_public_permissions
from cogs.logs import send_log_message

class Login(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @check_permissions("login_config")
    @app_commands.command(name="set_login", description="Configurer le système de login pour ce serveur.")
    @app_commands.describe(salon="Salon où sera envoyé le message d'invitation", role="Rôle à attribuer lors du login")
    async def set_login(self, interaction: discord.Interaction, salon: discord.TextChannel, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        login_ws = get_login_ws()
        guild_id = str(interaction.guild.id)

        all_rows = login_ws.get_all_values()
        existing = False
        for idx, row in enumerate(all_rows):
            if row[0] == guild_id:
                login_ws.update_cell(idx + 1, 2, str(salon.id))
                login_ws.update_cell(idx + 1, 3, str(role.id))
                existing = True
                break

        if not existing:
            login_ws.append_row([guild_id, str(salon.id), str(role.id)])

        # Message de login dans le salon choisi
        await salon.send(
            "Bonjour,\nAfin de vous enregistrer sur le serveur merci d'utiliser la commande ci-dessous:\n# __/login__"
        )

        await interaction.followup.send("Configuration du système de login enregistrée avec succès.", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a configuré le système de login - Salon : {salon.mention}, Rôle : {role.mention}")

    # /login
    @check_public_permissions("login")
    @app_commands.command(name="login", description="S'enregistrer sur le serveur.")
    @app_commands.describe(prenom="Votre prénom", nom="Votre nom", identifiant="Votre ID unique")
    async def login(self, interaction: discord.Interaction, prenom: str, nom: str, identifiant: str):
        await interaction.response.defer(ephemeral=True)

        login_ws = get_login_ws()
        guild_id = str(interaction.guild.id)

        all_rows = login_ws.get_all_values()
        config = next((row for row in all_rows if row[0] == guild_id), None)

        if not config:
            await interaction.followup.send("Aucune configuration de login trouvée pour ce serveur.", ephemeral=True)
            return

        salon_id = int(config[1])
        role_id = int(config[2])

        # Renommer l'utilisateur
        try:
            new_nick = f"{prenom} {nom} | {identifiant}"
            await interaction.user.edit(nick=new_nick)
        except discord.Forbidden:
            await interaction.followup.send("Je n'ai pas la permission de changer votre pseudo.", ephemeral=True)
            return

        # Ajouter le rôle
        role = interaction.guild.get_role(role_id)
        if role:
            await interaction.user.add_roles(role)
        else:
            await interaction.followup.send("Rôle introuvable sur le serveur.", ephemeral=True)
            return

        await interaction.followup.send(f"Bienvenue {prenom} ! Vous êtes maintenant enregistré.", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} s'est enregistré avec le pseudo {new_nick}")

    @check_permissions("remove_login_config")
    @app_commands.command(name="remove_login_config", description="Supprimer la configuration de login pour ce serveur.")
    async def remove_login_config(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        login_ws = get_login_ws()
        guild_id = str(interaction.guild.id)

        all_rows = login_ws.get_all_values()
        for idx, row in enumerate(all_rows):
            if row[0] == guild_id:
                login_ws.delete_rows(idx + 1)
                await interaction.followup.send("Configuration de login supprimée avec succès.", ephemeral=True)
                await send_log_message(interaction, f"{interaction.user} a supprimé la configuration du système de login")
                return

        await interaction.followup.send("Aucune configuration de login trouvée pour ce serveur.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Login(bot))
