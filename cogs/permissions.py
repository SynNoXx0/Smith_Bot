import discord
from discord import app_commands
from discord.ext import commands
from utils.sheet_utils import perms_ws  # Assure-toi que perms_ws pointe vers la bonne feuille
from utils.decorators import check_permissions, check_public_permissions

class Perms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /set_perms
    @check_permissions("set_perms")
    @app_commands.command(name="set_perms", description="Autoriser un rôle à utiliser une commande.")
    @app_commands.describe(commande="Nom de la commande", role="Rôle à autoriser")
    async def set_perms(self, interaction: discord.Interaction, commande: str, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        guild_id = str(interaction.guild.id)
        all_rows = perms_ws.get_all_values()

        updated = False
        for i, row in enumerate(all_rows):
            if row[0] == guild_id and row[1] == commande:
                roles = set(row[2].split(",")) if len(row) > 2 else set()
                roles.add(str(role.id))
                perms_ws.update_cell(i + 1, 3, ",".join(roles))
                updated = True
                break

        if not updated:
            perms_ws.append_row([guild_id, commande, str(role.id)])

        await interaction.followup.send(f"Le rôle {role.mention} a été autorisé à utiliser la commande `{commande}`.", ephemeral=True)

    # /remove_perms
    @check_permissions("remove_perms")
    @app_commands.command(name="remove_perms", description="Retirer l'autorisation d'un rôle pour une commande.")
    @app_commands.describe(commande="Nom de la commande", role="Rôle à retirer")
    async def remove_perms(self, interaction: discord.Interaction, commande: str, role: discord.Role):
        await interaction.response.defer(ephemeral=True)

        guild_id = str(interaction.guild.id)
        role_id = str(role.id)
        all_rows = perms_ws.get_all_values()

        # Debug: afficher les paramètres recherchés
        print(f"DEBUG: Recherche dans la feuille pour guild_id={guild_id}, command_name={commande}, role_id={role_id}")

        # On commence à la ligne 1 (pas la ligne d'en-tête)
        for i, row in enumerate(all_rows[1:], start=1):  # Ignorer la première ligne d'en-tête
            print(f"DEBUG: Vérification de la ligne {i}: {row}")  # Affiche chaque ligne

            # Vérification qu'il y a bien 3 colonnes dans la ligne
            if len(row) < 3:
                print(f"DEBUG: Ligne mal formée à l'index {i}, skipping...")
                continue  # Ignorer la ligne si elle ne contient pas assez de colonnes
            
            # Ajout du débogage pour voir les correspondances exactes
            print(f"DEBUG: Comparaison - guild_id: {row[0]} == {guild_id}, commande: {row[1]} == {commande}, role_id: {row[2]} == {role_id}")
            
            if row[0] == guild_id and row[1] == commande and row[2] == role_id:
                try:
                    print(f"DEBUG: Suppression de la ligne {i+1}")
                    # Suppression de la ligne à l'index i + 1 (les indices de Sheets commencent à 1)
                    perms_ws.delete_rows(i + 1, i + 1)  # Supprimer une seule ligne (de i+1 à i+1)
                    await interaction.followup.send(
                        f"Le rôle {role.mention} n’a plus accès à la commande `{commande}`. La ligne a été supprimée.",
                        ephemeral=True
                    )
                    return
                except Exception as e:
                    print(f"ERROR: Impossible de supprimer la ligne : {e}")
                    await interaction.followup.send(
                        f"Une erreur est survenue lors de la suppression de la ligne pour le rôle {role.mention}.",
                        ephemeral=True
                    )

        # Si aucune ligne correspondante n'est trouvée
        await interaction.followup.send(
            f"Aucune permission trouvée pour le rôle {role.mention} sur la commande `{commande}`.",
            ephemeral=True
        )

    # /see_perms
    @check_permissions("see_perms")
    @app_commands.command(name="see_perms", description="Voir les rôles ayant des permissions par commande.")
    async def see_perms(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild_id = str(interaction.guild.id)
        all_rows = perms_ws.get_all_values()

        embed = discord.Embed(title="Permissions par commande", color=discord.Color.blue())
        found = False

        for row in all_rows:
            if row[0] == guild_id:
                command_name = row[1]
                role_ids = row[2].split(",") if len(row) > 2 and row[2] else []
                roles_mentions = [f"<@&{rid}>" for rid in role_ids]
                embed.add_field(name=f"/{command_name}", value=", ".join(roles_mentions) or "Aucun rôle", inline=False)
                found = True

        if not found:
            embed.description = "Aucune permission définie pour ce serveur."

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Perms(bot))
