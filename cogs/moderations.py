import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
from utils.decorators import check_permissions, check_public_permissions
from cogs.logs import send_log_message

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /ban
    @check_permissions("ban")
    @app_commands.command(name="ban", description="Bannir un utilisateur.")
    @app_commands.describe(user="Utilisateur à bannir", raison="Raison du bannissement")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, raison: str):
        await interaction.response.defer(ephemeral=True)

        # Empêcher l'action sur soi-même ou sur un membre plus haut dans la hiérarchie
        if user == interaction.user:
            await interaction.followup.send("Tu ne peux pas utiliser cette commande sur toi-même.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.followup.send("Tu ne peux pas modérer un membre avec un rôle supérieur ou égal au tien.", ephemeral=True)
            return
        try:
            await user.ban(reason=raison)
            await interaction.followup.send(f"{user} a été banni. Raison : {raison}")
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du bannissement : {e}")
    

    # /ban_list
    @check_permissions("ban_list")
    @app_commands.command(name="ban_list", description="Afficher la liste des utilisateurs bannis.")
    async def ban_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # Defer pour ne pas laisser l'utilisateur dans l'attente

        # Récupérer la liste des bannis
        bans = [entry async for entry in interaction.guild.bans()]
        
        if not bans:
            await interaction.followup.send("✅ Aucun utilisateur n'est banni.", ephemeral=True)
            return

        # Création d'une chaîne de caractères contenant la liste des bannis
        ban_list_str = "\n".join(
            f"- {entry.user.name}#{entry.user.discriminator} : {entry.reason or 'Aucune raison'}" for entry in bans
        )
        
        # Création d'un embed pour afficher la liste de manière plus propre
        embed = discord.Embed(title="Utilisateurs Bannis", description=ban_list_str, color=discord.Color.red())
        
        # Envoi du message contenant l'embed avec la liste des bannis
        await interaction.followup.send(embed=embed, ephemeral=True)

    # /unban
    @check_permissions("unban")
    @app_commands.command(name="unban", description="Débannir un utilisateur.")
    @app_commands.describe(nom_membre="Nom#Tag ou juste Nom")
    async def unban(self, interaction: discord.Interaction, nom_membre: str):
        try:
            # Récupération de la liste des bannis
            bans = [entry async for entry in interaction.guild.bans()]

            # Vérifie si un tag est fourni
            if '#' in nom_membre:
                try:
                    name, tag = nom_membre.split('#')
                except ValueError:
                    await interaction.response.send_message("❌ Format invalide. Utilisez Nom#Tag ou juste Nom.", ephemeral=True)
                    return

                for entry in bans:
                    if entry.user.name == name and entry.user.discriminator == tag:
                        await interaction.guild.unban(entry.user)
                        await interaction.response.send_message(f"✅ {entry.user} a été débanni.", ephemeral=True)
                        await send_log_message(interaction, f"{interaction.user} a débanni {entry.user}")
                        return

            else:
                for entry in bans:
                    if entry.user.name == nom_membre:
                        await interaction.guild.unban(entry.user)
                        await interaction.response.send_message(f"✅ {entry.user} a été débanni.", ephemeral=True)
                        await send_log_message(interaction, f"{interaction.user} a débanni {entry.user}")
                        return

            # Si l'utilisateur n'est pas trouvé dans la liste des bannis
            await interaction.response.send_message("❌ Utilisateur non trouvé dans les bannis.", ephemeral=True)

        except Exception as e:
            # Gérer toute exception qui pourrait survenir
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Une erreur s’est produite.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Une erreur s’est produite après la réponse initiale.", ephemeral=True)

            print("Erreur dans la commande unban :", e)

    # /kick
    @check_permissions("kick")
    @app_commands.command(name="kick", description="Expulser un utilisateur.")
    @app_commands.describe(user="Utilisateur à expulser", raison="Raison du kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, raison: str):
        await interaction.response.defer(ephemeral=True)
        # Empêcher l'action sur soi-même ou sur un membre plus haut dans la hiérarchie
        if user == interaction.user:
            await interaction.followup.send("Tu ne peux pas utiliser cette commande sur toi-même.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.followup.send("Tu ne peux pas modérer un membre avec un rôle supérieur ou égal au tien.", ephemeral=True)
            return
        try:
            await user.kick(reason=raison)
            await interaction.followup.send(f"{user} a été expulsé. Raison : {raison}")
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du kick : {e}")

    # /mute
    @check_permissions("mute")
    @app_commands.command(name="timeout", description="Exclure un utilisateur pendant une durée définie.")
    @app_commands.describe(user="Utilisateur à mute", durée="Durée en minutes", raison="Raison du mute")
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, durée: int, raison: str):
        await interaction.response.defer(ephemeral=True)
        # Empêcher l'action sur soi-même ou sur un membre plus haut dans la hiérarchie
        if user == interaction.user:
            await interaction.followup.send("Tu ne peux pas utiliser cette commande sur toi-même.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.followup.send("Tu ne peux pas modérer un membre avec un rôle supérieur ou égal au tien.", ephemeral=True)
            return
        try:
            duration = timedelta(minutes=durée)
            await user.timeout(duration, reason=raison)
            await interaction.followup.send(f"{user} a été mute pendant {durée} minute(s). Raison : {raison}")
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du mute : {e}")

    # /unmute
    @check_permissions("untimeout")
    @app_commands.command(name="untimeout", description="Retirer le mute d'un utilisateur.")
    @app_commands.describe(user="Utilisateur à unmute")
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        # Empêcher l'action sur soi-même ou sur un membre plus haut dans la hiérarchie
        if user == interaction.user:
            await interaction.followup.send("Tu ne peux pas utiliser cette commande sur toi-même.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.followup.send("Tu ne peux pas modérer un membre avec un rôle supérieur ou égal au tien.", ephemeral=True)
            return
        try:
            await user.timeout(None)
            await interaction.followup.send(f"{user} a été unmute.")
        except Exception as e:
            await interaction.followup.send(f"Erreur lors du unmute : {e}")

    # /clear
    @check_permissions("clear")
    @app_commands.command(name="clear", description="Supprimer des messages")
    @app_commands.describe(nombre="Nombre de messages à supprimer")
    async def clear(self, interaction: discord.Interaction, nombre: int):
        """Supprimer un certain nombre de messages dans le canal."""
        await interaction.response.defer(ephemeral=True)
        # Vérifier si le nombre est valide
        if nombre <= 0 or nombre > 100:
            await interaction.followup.send("❌ Veuillez spécifier un nombre de messages entre 1 et 100.", ephemeral=True)
            return

        # Purger les messages
        deleted = await interaction.channel.purge(limit=nombre)
        
        # Confirmation
        await interaction.followup.send(f"✅ {len(deleted)} messages ont été supprimés.", ephemeral=True)
        
        # Log dans le salon de logs (si configuré)
        await send_log_message(interaction, f"{interaction.user} a supprimé {len(deleted)} messages.")

    # /serverinfo
    @check_public_permissions("serverinfo")
    @app_commands.command(name="serverinfo", description="Afficher des informations sur le serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)  # Pour indiquer qu'on répondra plus tard

            guild = interaction.guild
            embed = discord.Embed(
                title=f"Informations sur {guild.name}",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            embed.add_field(name="Nom", value=guild.name, inline=True)
            embed.add_field(name="ID", value=guild.id, inline=True)
            embed.add_field(name="Membres", value=guild.member_count, inline=True)
            embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
            embed.set_footer(text=f"Demandé par {interaction.user}", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)
            print(f"[ERREUR serverinfo] : {e}")

    # /slowmode
    @check_permissions("slowmode")
    @app_commands.command(name="slowmode", description="Définit le délai entre les messages (mode lent) dans le salon.")
    @app_commands.describe(duree="Durée du mode lent en secondes (entre 0 et 21600)")
    async def slowmode(self, interaction: discord.Interaction, duree: int):
        await interaction.response.defer(ephemeral=True)

        if duree < 0 or duree > 21600:
            await interaction.followup.send("❌ La durée doit être entre 0 et 21600 secondes (6 heures).", ephemeral=True)
            return

        try:
            await interaction.channel.edit(slowmode_delay=duree)
            await interaction.followup.send(
                f"✅ Mode lent défini à {duree} seconde(s) dans ce salon.",
                ephemeral=True
            )
        except Exception as e:
            print(f"[ERREUR /slowmode] : {e}")
            await interaction.followup.send("❌ Une erreur s’est produite en appliquant le mode lent.", ephemeral=True)
    
    # /nick
    @check_permissions("nick")
    @app_commands.command(name="nick", description="Changer le pseudo d'un membre")
    @app_commands.describe(member="Le membre dont changer le pseudo", nickname="Le nouveau pseudo à appliquer")
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str):
        # Permission check
        if not interaction.user.guild_permissions.manage_nicknames:
            await interaction.response.send_message("❌ Vous n'avez pas la permission de gérer les pseudos.", ephemeral=True)
            return

        try:
            await member.edit(nick=nickname)
            await interaction.response.send_message(f"✅ Le pseudo de {member.mention} a été changé en **{nickname}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Je n'ai pas la permission de changer le pseudo de ce membre.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : `{e}`", ephemeral=True)

    # /purge
    @check_permissions("purge")
    @app_commands.command(name="purge", description="Supprimer les messages d'un utilisateur dans ce salon")
    @app_commands.describe(member="Le membre dont tu veux supprimer les messages", limit="Nombre maximum de messages à analyser (max 1000)")
    async def purge(self, interaction: discord.Interaction, member: discord.Member, limit: int = 100):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Vous n'avez pas la permission de gérer les messages.", ephemeral=True)
            return

        if limit > 1000 or limit < 1:
            await interaction.response.send_message("❌ La limite doit être comprise entre 1 et 1000.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        def is_user_message(msg):
            return msg.author == member

        deleted = await interaction.channel.purge(limit=limit, check=is_user_message, bulk=True)

        await interaction.followup.send(f"✅ {len(deleted)} messages de {member.mention} ont été supprimés.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
