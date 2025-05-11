import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.sheet_utils import get_worksheet
from utils.decorators import check_permissions, check_public_permissions

class Absences(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_absences.start()

    def cog_unload(self):
        self.check_absences.cancel()

    @check_permissions("absence_config")
    @app_commands.command(name="absence_config", description="Définit le rôle à ajouter lors d'une absence")
    @app_commands.describe(role="Rôle à attribuer lors de l'absence")
    @commands.has_permissions(manage_roles=True)
    async def absence_config(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        # Accéder à la feuille absences_config pour récupérer le rôle configuré
        sheet = get_worksheet("absences_config")
        all_rows = sheet.get_all_values()
        headers = all_rows[0]
        rows = all_rows[1:]

        updated = False
        for i, row in enumerate(rows, start=2):
            if row[0] == str(interaction.guild.id):
                sheet.update_cell(i, 2, str(role.id))  # Mise à jour de l'ID du rôle
                updated = True
                break

        if not updated:
            sheet.append_row([str(interaction.guild.id), str(role.id)])  # Ajouter un nouveau rôle

        await interaction.followup.send(f"✅ Le rôle {role.mention} sera maintenant attribué lors d'une absence.", ephemeral=True)

    @check_public_permissions("absent")
    @app_commands.command(name="absent", description="Déclare une absence")
    @app_commands.describe(raison="Raison de l'absence", duree="Durée en jours")
    async def absent(self, interaction: discord.Interaction, raison: str, duree: int):
        await interaction.response.defer()

        if duree <= 0 or duree > 365:
            await interaction.followup.send("❌ Durée invalide. Entre 1 et 365 jours.", ephemeral=True)
            return

        # Obtenir le rôle configuré
        config_sheet = get_worksheet("absences_config")
        config = config_sheet.get_all_records()
        role_id = None
        for row in config:
            if str(row["guild_id"]) == str(interaction.guild.id):
                role_id = int(row["role_to_add_id"])
                break

        if not role_id:
            await interaction.followup.send("❌ Aucun rôle d'absence configuré. Utilisez /absence_config pour le définir.", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.followup.send("❌ Le rôle configuré n'existe plus sur ce serveur.", ephemeral=True)
            return

        await interaction.user.add_roles(role, reason="Absence déclarée")
        date_fin = (datetime.utcnow() + timedelta(days=duree)).strftime("%d-%m-%Y")

        # Sauvegarde dans la feuille "absence"
        absence_sheet = get_worksheet("absences")
        absence_sheet.append_row([str(interaction.user.id), str(interaction.guild.id), date_fin])

        embed = discord.Embed(
            title="📌 Absence déclarée",
            description=f"👤 {interaction.user.mention}\n📝 {raison}\n📅 Fin prévue : {date_fin}",
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @tasks.loop(hours=12)
    async def check_absences(self):
        # Utiliser le nom correct de la feuille ("absences")
        absence_sheet = get_worksheet("absences")
        
        if not absence_sheet:
            print("Erreur : La feuille 'absences' n'a pas pu être récupérée.")
            return  # Ne pas continuer si la feuille est introuvable

        config_sheet = get_worksheet("absences_config")
        config_data = {str(row["guild_id"]): int(row["role_to_add_id"]) for row in config_sheet.get_all_records()}

        data = absence_sheet.get_all_records()
        today = datetime.utcnow().date()
        rows_to_remove = []

        for i, row in enumerate(data, start=2):  # ligne 2 = première ligne de données
            user_id = int(row["user_id"])
            guild_id = int(row["guild_id"])
            date_fin = datetime.strptime(row["date_fin"], "%d-%m-%Y").date()

            if today >= date_fin:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                member = guild.get_member(user_id)
                if not member:
                    continue

                role_id = config_data.get(str(guild_id))
                if not role_id:
                    continue
                role = guild.get_role(role_id)
                if role and role in member.roles:
                    await member.remove_roles(role, reason="Fin d'absence")

                rows_to_remove.append(i)

        # Supprimer les lignes inversément pour ne pas décaler les indices
        for i in reversed(rows_to_remove):
            absence_sheet.delete_rows(i)

    @check_absences.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @check_public_permissions("absence_stop")
    @app_commands.command(name="absence_stop", description="Annule ton absence en cours")
    async def absence_stop(self, interaction: discord.Interaction):
        await interaction.response.defer()

        absence_sheet = get_worksheet("absences")
        config_sheet = get_worksheet("absences_config")

        # Vérifie si l'utilisateur a une absence active
        all_rows = absence_sheet.get_all_records()
        user_row_index = None
        for index, row in enumerate(all_rows, start=2):
            if str(row["user_id"]) == str(interaction.user.id) and str(row["guild_id"]) == str(interaction.guild.id):
                user_row_index = index
                break

        if not user_row_index:
            await interaction.followup.send("❌ Vous n'avez pas d'absence active.", ephemeral=True)
            return

        # Retirer le rôle
        role_id = None
        config_data = config_sheet.get_all_records()
        for row in config_data:
            if str(row["guild_id"]) == str(interaction.guild.id):
                role_id = int(row["role_to_add_id"])
                break

        if not role_id:
            await interaction.followup.send("❌ Aucun rôle d'absence configuré sur ce serveur.", ephemeral=True)
            return

        role = interaction.guild.get_role(role_id)
        if role and role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Fin d'absence manuelle")

        # Supprimer la ligne d'absence
        absence_sheet.delete_rows(user_row_index)

        embed = discord.Embed(
            title="✅ Fin d'absence",
            description=f"👤 {interaction.user.mention} a mis fin à son absence.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)


    @check_permissions("absence_list")
    @app_commands.command(name="absence_list", description="📋 Liste des personnes actuellement absentes")
    async def absence_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        sheet = get_worksheet("absences")
        data = sheet.get_all_records()

        absents = [
            f"<@{row['user_id']}> — fin le `{row['date_fin']}`"
            for row in data
            if str(row['guild_id']) == str(interaction.guild.id)
        ]

        if not absents:
            await interaction.followup.send("✅ Personne n'est actuellement en absence.", ephemeral=True)
        else:
            embed = discord.Embed(
                title="📋 Liste des absents",
                description="\n".join(absents),
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @check_permissions("absence_info")
    @app_commands.command(name="absence_info", description="ℹ️ Voir les infos d'absence d'un membre")
    @app_commands.describe(user="Utilisateur à vérifier")
    async def absence_info(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        sheet = get_worksheet("absences")
        data = sheet.get_all_records()

        for row in data:
            if str(row["user_id"]) == str(user.id) and str(row["guild_id"]) == str(interaction.guild.id):
                embed = discord.Embed(
                    title="📌 Informations d'absence",
                    description=f"👤 {user.mention}\n📅 Fin prévue : `{row['date_fin']}`",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

        await interaction.followup.send(f"❌ {user.mention} n'est pas actuellement absent.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Absences(bot))
