import discord
from discord import app_commands
from discord.ext import commands
from utils.decorators import check_permissions, check_public_permissions
from cogs.logs import send_log_message
import asyncio

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /poll
    @check_permissions("sondage")
    @app_commands.command(name="sondage", description="Créer un sondage avec plusieurs options.")
    @app_commands.describe(
        message="Question du sondage",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3",
        option4="Option 4",
        option5="Option 5",
        option6="Option 6",
        option7="Option 7",
        option8="Option 8",
        option9="Option 9",
        option10="Option 10"
    )
    async def sondage(
        self,
        interaction: discord.Interaction,
        message: str,
        option1: str,
        option2: str,
        option3: str = None,
        option4: str = None,
        option5: str = None,
        option6: str = None,
        option7: str = None,
        option8: str = None,
        option9: str = None,
        option10: str = None,
    ):
        await interaction.response.defer(ephemeral=True)

        options = [opt for opt in [option1, option2, option3, option4, option5,
                                   option6, option7, option8, option9, option10] if opt]

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        if len(options) < 2:
            await interaction.followup.send("❌ Veuillez fournir au moins deux options.", ephemeral=True)
            return

        if len(options) > 10:
            await interaction.followup.send("❌ Maximum 10 options autorisées.", ephemeral=True)
            return

        description = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
        embed = discord.Embed(title=message, description=description, color=discord.Color.blurple())
        embed.set_footer(text=f"Sondage lancé par {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        poll_msg = await interaction.channel.send(embed=embed)

        for i in range(len(options)):
            await poll_msg.add_reaction(emojis[i])

        await interaction.followup.send("✅ Sondage créé avec succès !", ephemeral=True)

    # /suggest
    @check_public_permissions("suggestion")
    @app_commands.command(name="suggestion", description="Envoyer une suggestion.")
    @app_commands.describe(message="Votre suggestion")
    async def suggestion(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)  # Différer la réponse
        await asyncio.sleep(1)  # Attendre un court instant (1 seconde) pour simuler un traitement si nécessaire
        embed = discord.Embed(title="💡 Suggestion", description=message, color=discord.Color.green())
        embed.set_footer(text=f"Suggestion de {interaction.user}")
        
        # Utilisation de followup pour envoyer le message
        await interaction.followup.send(embed=embed)
        await interaction.followup.send("✅ Suggestion envoyée avec succès !", ephemeral=True)
        
        # Envoi du log
        await send_log_message(interaction, f"{interaction.user} a envoyé une suggestion : {message}")

    # /avis
    @check_public_permissions("avis")
    @app_commands.command(name="avis", description="Donner un avis sur un employé.")
    @app_commands.describe(
        employe="Nom de l'employé",
        note="Note sur 5 (1 = mauvais, 5 = excellent)",
        message="Votre avis"
    )
    async def avis(self, interaction: discord.Interaction, employe: str, note: int, message: str):
        await interaction.response.defer(ephemeral=True)  # Différer la réponse
        await asyncio.sleep(1)  # Attendre un court instant (1 seconde) pour simuler un traitement si nécessaire

        if note < 1 or note > 5:
            await interaction.followup.send("❌ La note doit être comprise entre 1 et 5.", ephemeral=True)
            return

        stars = "⭐" * note + "☆" * (5 - note)

        embed = discord.Embed(title="📝 Avis sur un employé", color=discord.Color.orange())
        embed.add_field(name="👤 Employé", value=employe, inline=True)
        embed.add_field(name="⭐ Note", value=stars, inline=True)
        embed.add_field(name="💬 Avis", value=message, inline=False)
        embed.set_footer(text=f"Avis laissé par {interaction.user}")

        await interaction.followup.send(embed=embed)
        await interaction.followup.send("✅ Avis envoyé avec succès.", ephemeral=True)
        
        await send_log_message(interaction, f"{interaction.user} a donné un avis sur {employe} : {stars} - {message}")

    @check_public_permissions("patchnote")
    @app_commands.command(name="patchnote", description="Affiche le dernier changelog.")
    async def patchnote(self, interaction: discord.Interaction):
        guild_id = 1370019626766827622
        channel_id = 1370032014253756537

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await interaction.response.send_message("❌ Impossible d'accéder au serveur cible.", ephemeral=True)

        channel = guild.get_channel(channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ Impossible d'accéder au salon de changelog.", ephemeral=True)

        try:
            messages = [message async for message in channel.history(limit=1)]
            if not messages:
                return await interaction.response.send_message("ℹ️ Aucun message trouvé dans le salon de patchnote.", ephemeral=True)

            latest_message = messages[0]
            embed = discord.Embed(
                title="📝 Dernier patchnote",
                description=latest_message.content,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Publié par {latest_message.author}", icon_url=latest_message.author.display_avatar.url)

            await interaction.response.send_message(embed=embed)
            await send_log_message(interaction, f"{interaction.user} a consulté le dernier patchnote")
        except discord.Forbidden:
            await interaction.response.send_message("❌ Le bot n'a pas la permission de lire l'historique du salon.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Une erreur est survenue : {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Community(bot))