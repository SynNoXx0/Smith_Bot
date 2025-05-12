import discord
from discord import app_commands
from discord.ext import commands
from utils.decorators import check_permissions, check_public_permissions
from cogs.logs import send_log_message

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /ping
    @check_public_permissions("ping")
    @app_commands.command(name="ping", description="Affiche la latence du bot.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # en millisecondes
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"Latence du bot : **{latency}ms**",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requête faite par {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a vérifié la latence du bot : {latency}ms")

    # /support
    @check_public_permissions("support")
    @app_commands.command(name="support", description="Obtiens le lien vers le serveur de support.")
    async def support(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛠️ Besoin d'aide ?",
            description="[Clique ici pour rejoindre le serveur de support](https://discord.gg/9frUpwdbKh)",
            color=discord.Color.green()
        )
        embed.set_footer(text="Support du bot")
        await interaction.response.send_message(embed=embed, ephemeral=True)  # visible uniquement par l'utilisateur
        await send_log_message(interaction, f"{interaction.user} a demandé le lien du serveur de support")


async def setup(bot):
    await bot.add_cog(Help(bot))