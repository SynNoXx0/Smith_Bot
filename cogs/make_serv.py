import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal
from utils.decorators import check_permissions
from cogs.logs import send_log_message

class MakeServ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Liste des modèles disponibles
    MODELS = {
        "Legal": {
            "𝐀𝐜𝐜𝐮𝐞𝐢𝐥𝐥𝐞": ["🛬｜𝐀𝐫𝐫𝐢𝐯𝐚𝐧𝐭", "✅｜𝐄𝐧𝐫𝐞𝐠𝐢𝐬𝐭𝐫𝐞𝐦𝐞𝐧𝐭"],
            "𝐈𝐧𝐟𝐨𝐫𝐦𝐚𝐭𝐢𝐨𝐧𝐬": ["📢｜𝐀𝐧𝐧𝐨𝐧𝐜𝐞𝐬", "🏛｜𝐥𝐨𝐜𝐚𝐥𝐢𝐬𝐚𝐭𝐢𝐨𝐧", "🔔｜𝐍𝐨𝐭𝐢𝐟𝐢𝐜𝐚𝐭𝐢𝐨𝐧𝐬", "💼｜𝐑𝐞𝐜𝐫𝐮𝐭𝐞𝐦𝐞𝐧𝐭", "⭐｜𝐀𝐯𝐢𝐬"],
            "𝐆𝐞́𝐧𝐞́𝐫𝐚𝐥": ["💭｜𝐃𝐢𝐬𝐜𝐮𝐬𝐬𝐢𝐨𝐧", "🎞｜𝐏𝐡𝐨𝐭𝐨-𝐕𝐢𝐝𝐞́𝐨", "💡｜𝐬𝐮𝐠𝐠𝐞𝐬𝐭𝐢𝐨𝐧", "🎙 ｜𝐑𝐚𝐝𝐢𝐨"],
            "𝐈𝐧𝐟𝐨𝐫𝐦𝐚𝐭𝐢𝐨𝐧𝐬 𝐞𝐦𝐩𝐥𝐨𝐲𝐞𝐫": ["📢｜𝐀𝐧𝐧𝐨𝐧𝐜𝐞𝐬", "📊｜𝐔𝐩-𝐃𝐨𝐰𝐧", "🚨｜𝐀𝐯𝐞𝐫𝐭𝐢𝐬𝐬𝐞𝐦𝐞𝐧𝐭", "🚨｜𝐂𝐨𝐧𝐯𝐨𝐜𝐚𝐭𝐢𝐨𝐧𝐬", "📁｜𝐃𝐨𝐜𝐮𝐦𝐞𝐧𝐭𝐬"],
            "𝐆𝐞́𝐧𝐞́𝐫𝐚𝐥 𝐞𝐦𝐩𝐥𝐨𝐲𝐞𝐫": ["💭｜𝐃𝐢𝐬𝐜𝐮𝐬𝐬𝐢𝐨𝐧", "🎞️｜𝐏𝐡𝐨𝐭𝐨-𝐕𝐢𝐝𝐞́𝐨", "💡｜𝐬𝐮𝐠𝐠𝐞𝐬𝐭𝐢𝐨𝐧", "❌｜𝐀𝐛��𝐞𝐧𝐜𝐞𝐬", "🎙️ ｜𝐑𝐚𝐝𝐢𝐨 𝟏", "🎙️ ｜𝐑𝐚𝐝𝐢𝐨 𝟐"]
        },
        # D'autres modèles peuvent être ajoutés ici
    }

    @check_permissions("make_serv")
    @app_commands.command(name="make_serv", description="Créer la structure du serveur selon un modèle")
    @app_commands.describe(model="Modèle de serveur à appliquer")
    async def make_serv(
        self,
        interaction: discord.Interaction,
        model: Literal["Legal"]  # Ajoute ici les noms des modèles disponibles
    ):
        await interaction.response.defer(ephemeral=True)

        structure = self.MODELS.get(model)
        if not structure:
            await interaction.followup.send("❌ Modèle introuvable.", ephemeral=True)
            return

        try:
            for category_name, channels in structure.items():
                category = await interaction.guild.create_category(name=category_name)
                for channel_name in channels:
                    if "🎙" in channel_name:
                        await interaction.guild.create_voice_channel(name=channel_name, category=category)
                    else:
                        await interaction.guild.create_text_channel(name=channel_name, category=category)

            await interaction.followup.send(f"✅ Le serveur a été configuré avec le modèle **{model}**.", ephemeral=True)
            await send_log_message(interaction, f"{interaction.user} a configuré le serveur avec le modèle {model}")
        except Exception as e:
            print("[ERREUR make_serv] :", e)
            await interaction.followup.send("❌ Une erreur est survenue lors de la création.", ephemeral=True)

    @check_permissions("reset_serv")
    @app_commands.command(name="reset_serv", description="❌ Supprime tous les salons et catégories du serveur")
    async def reset_serv(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await interaction.followup.send(
            "⚠️ Cette commande va **supprimer tous les salons et catégories** du serveur.\n"
            "Tape `CONFIRMER` dans les 15 secondes pour valider.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.content == "CONFIRMER" and msg.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=15.0, check=check)
        except:
            return await interaction.followup.send("⏱️ Temps écoulé, annulation de la commande.", ephemeral=True)

        # Supprimer tous les salons
        for channel in interaction.guild.channels:
            try:
                await channel.delete()
            except:
                pass

        await interaction.followup.send("✅ Tous les salons et catégories ont été supprimés avec succès.", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a réinitialisé la structure du serveur")

async def setup(bot):
    await bot.add_cog(MakeServ(bot))
