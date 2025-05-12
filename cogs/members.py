import discord
from discord import app_commands
from discord.ext import commands
from utils.sheet_utils import get_worksheet
from utils.decorators import check_permissions
from cogs.logs import send_log_message

class MemberEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_config(self, guild_id):
        sheet = get_worksheet("join_leave_config")
        all_rows = sheet.get_all_records()
        for row in all_rows:
            if str(row["guild_id"]) == str(guild_id):
                return row
        return None

    def update_config(self, guild_id, column_name, channel_id):
        sheet = get_worksheet("join_leave_config")
        all_rows = sheet.get_all_values()
        headers = all_rows[0]
        rows = all_rows[1:]

        col_index = headers.index(column_name) + 1
        for i, row in enumerate(rows, start=2):
            if row[0] == str(guild_id):
                sheet.update_cell(i, col_index, str(channel_id))
                return

        # Si pas trouvé, ajouter une nouvelle ligne
        new_row = [str(guild_id), "", ""]
        if column_name == "arrival_channel_id":
            new_row[1] = str(channel_id)
        elif column_name == "departure_channel_id":
            new_row[2] = str(channel_id)
        sheet.append_row(new_row)

    @check_permissions("set_join_message")
    @app_commands.command(name="set_join_message", description="Définit le salon pour les messages d'arrivée.")
    async def set_join_message(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.update_config(interaction.guild.id, "arrival_channel_id", channel.id)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"✅ Salon d'arrivée défini sur {channel.mention}", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a configuré le salon d'arrivée sur {channel.mention}")

    @check_permissions("set_leave_message")
    @app_commands.command(name="set_leave_message", description="Définit le salon pour les messages de départ.")
    async def set_leave_message(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.update_config(interaction.guild.id, "departure_channel_id", channel.id)
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(f"✅ Salon de départ défini sur {channel.mention}", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a configuré le salon de départ sur {channel.mention}")

    @check_permissions("autorole")
    @app_commands.command(name="autorole", description="Configurer les rôles automatiques")
    @app_commands.describe(
        action="L'action à effectuer (add/remove/list)",
        role="Le rôle à ajouter/retirer (uniquement pour add/remove)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list")
    ])
    async def autorole(self, interaction: discord.Interaction, action: str, role: discord.Role = None):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Récupérer la feuille de calcul
            sheet = get_worksheet("autoroles")
            all_autoroles = sheet.get_all_records()
            
            # Debug: Afficher les données reçues
            print(f"Données de la feuille: {all_autoroles}")
            
            # Trouver la configuration pour ce serveur
            server_config = None
            for config in all_autoroles:
                try:
                    if int(config["server_id"]) == interaction.guild_id:
                        server_config = config
                        break
                except (ValueError, KeyError) as e:
                    print(f"Erreur lors de la lecture de la configuration: {e}")
                    continue
            
            # Debug: Afficher la configuration trouvée
            print(f"Configuration du serveur: {server_config}")
            
            if action == "add":
                if not role:
                    await interaction.followup.send("❌ Vous devez spécifier un rôle à ajouter.", ephemeral=True)
                    return
                    
                if not server_config:
                    # Créer une nouvelle configuration
                    new_config = {
                        "server_id": str(interaction.guild_id),
                        "roles": str(role.id)
                    }
                    sheet.append_row([new_config["server_id"], new_config["roles"]])
                else:
                    # Ajouter le rôle à la liste existante
                    current_roles = str(server_config["roles"]).split(",") if server_config["roles"] else []
                    if str(role.id) in current_roles:
                        await interaction.followup.send(f"❌ Le rôle {role.mention} est déjà dans la liste des rôles automatiques.", ephemeral=True)
                        return
                        
                    current_roles.append(str(role.id))
                    # Mettre à jour la configuration
                    row_index = all_autoroles.index(server_config) + 2  # +2 car l'index commence à 0 et il y a l'en-tête
                    sheet.update_cell(row_index, 2, ",".join(current_roles))
                
                await interaction.followup.send(f"✅ Le rôle {role.mention} a été ajouté aux rôles automatiques.", ephemeral=True)
                await send_log_message(interaction, f"{interaction.user} a ajouté le rôle {role.mention} aux rôles automatiques")
                
            elif action == "remove":
                if not role:
                    await interaction.followup.send("❌ Vous devez spécifier un rôle à retirer.", ephemeral=True)
                    return
                    
                if not server_config:
                    await interaction.followup.send("❌ Aucun rôle automatique n'est configuré sur ce serveur.", ephemeral=True)
                    return
                    
                current_roles = str(server_config["roles"]).split(",") if server_config["roles"] else []
                if str(role.id) not in current_roles:
                    await interaction.followup.send(f"❌ Le rôle {role.mention} n'est pas dans la liste des rôles automatiques.", ephemeral=True)
                    return
                    
                current_roles.remove(str(role.id))
                # Mettre à jour la configuration
                row_index = all_autoroles.index(server_config) + 2
                if current_roles:
                    sheet.update_cell(row_index, 2, ",".join(current_roles))
                else:
                    sheet.delete_rows(row_index)
                    
                await interaction.followup.send(f"✅ Le rôle {role.mention} a été retiré des rôles automatiques.", ephemeral=True)
                await send_log_message(interaction, f"{interaction.user} a retiré le rôle {role.mention} des rôles automatiques")
                
            elif action == "list":
                # Debug: Afficher les informations de débogage
                print(f"Action: list")
                print(f"Server ID: {interaction.guild_id}")
                print(f"Server Config: {server_config}")
                
                if not server_config:
                    await interaction.followup.send("❌ Aucun rôle automatique n'est configuré sur ce serveur.", ephemeral=True)
                    return
                
                roles_str = str(server_config.get("roles", ""))
                if not roles_str:
                    await interaction.followup.send("❌ Aucun rôle automatique n'est configuré sur ce serveur.", ephemeral=True)
                    return
                
                print(f"Rôles trouvés: {roles_str}")
                roles = []
                for role_id in roles_str.split(","):
                    try:
                        role = interaction.guild.get_role(int(role_id))
                        if role:
                            roles.append(role.mention)
                        else:
                            print(f"Rôle non trouvé: {role_id}")
                    except ValueError as e:
                        print(f"Erreur lors de la conversion du rôle {role_id}: {e}")
                        continue
                    
                if not roles:
                    await interaction.followup.send("❌ Aucun rôle automatique valide n'est configuré sur ce serveur.", ephemeral=True)
                    return
                    
                embed = discord.Embed(
                    title="📋 Liste des Rôles Automatiques",
                    description="\n".join(roles),
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                await send_log_message(interaction, f"{interaction.user} a consulté la liste des rôles automatiques")
                
        except Exception as e:
            print(f"Erreur lors de l'exécution de la commande autorole: {e}")
            await interaction.followup.send("❌ Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Gestion des messages de bienvenue
        config = self.get_config(member.guild.id)
        if config and config.get("arrival_channel_id"):
            channel = self.bot.get_channel(int(config["arrival_channel_id"]))
            if channel:
                embed = discord.Embed(
                    title="🎉 Nouvelle arrivée !",
                    description=f"Bienvenue {member.mention} !",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                await channel.send(embed=embed)

        # Gestion des rôles automatiques
        sheet = get_worksheet("autoroles")
        all_autoroles = sheet.get_all_records()
        server_config = next((c for c in all_autoroles if c["server_id"] == str(member.guild.id)), None)
        
        if server_config and server_config["roles"]:
            for role_id in server_config["roles"].split(","):
                role = member.guild.get_role(int(role_id))
                if role:
                    try:
                        await member.add_roles(role)
                    except discord.Forbidden:
                        print(f"Impossible d'ajouter le rôle {role.name} à {member.name} - Permissions insuffisantes")
                    except Exception as e:
                        print(f"Erreur lors de l'ajout du rôle {role.name} à {member.name}: {str(e)}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = self.get_config(member.guild.id)
        if config and config.get("departure_channel_id"):
            channel = self.bot.get_channel(int(config["departure_channel_id"]))
            if channel:
                embed = discord.Embed(
                    title="👋 Départ du serveur",
                    description=f"{member.mention} a quitté le serveur.",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemberEvents(bot))