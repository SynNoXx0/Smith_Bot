import discord
from discord.ext import commands
from discord.ui import View, button
import asyncio
from utils.decorators import check_permissions, require_grade
from cogs.logs import send_log_message

class EmbedBuilder(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = discord.Embed()
        self.current_step = 0
        self.author_name = None
        self.author_url = None
        self.footer_text = None
        self.temp_field_name = None

        self.steps = [
            "Entrez le nom de l'**Auteur** (ou skip) :",
            "Entrez l'URL de l'**Auteur** (ou skip) :",
            "Entrez l'icône de l'**Auteur** (ou skip) :",
            "Entrez le **Titre** (ou skip) :",
            "Entrez la **Description** (ou skip) :",
            "Entrez l'URL de l'embed (ou skip) :",
            "Entrez la **Couleur** (#HEX) :",
            "Souhaitez-vous ajouter un champ ? (oui/non)",
            "Entrez le **Nom** du champ :",
            "Entrez la **Valeur** du champ :",
            "Ajouter un autre champ ? (oui/non)",
            "URL de l'**Image** (ou skip) :",
            "URL de la **Miniature** (ou skip) :",
            "Texte du **Footer** (ou skip) :",
            "Icône du **Footer** (ou skip) :",
            "Ajouter un **Timestamp** ? (oui/non)",
            "Envoyer l'embed ? (oui/non)"
        ]

    async def send_step(self, interaction, step):
        await interaction.followup.send(step, ephemeral=True)

    async def wait_for_input(self, interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
            await msg.delete()
            return msg.content
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Temps écoulé, veuillez recommencer.", ephemeral=True)
            self.stop()
            return "skip"

    async def update_embed_display(self, interaction):
        if self.embed.title is None:
            self.embed.title = "Titre non défini"
        await interaction.followup.send(embed=self.embed, ephemeral=True)

    async def process_step(self, interaction):
        if self.current_step >= len(self.steps):
            return

        await self.send_step(interaction, self.steps[self.current_step])
        response = await self.wait_for_input(interaction)

        if response.lower() != "skip":
            match self.current_step:
                case 0:
                    self.author_name = response
                case 1:
                    self.author_url = response
                case 2:
                    self.embed.set_author(
                        name=self.author_name or discord.Embed.Empty,
                        url=self.author_url or discord.Embed.Empty,
                        icon_url=response
                    )
                case 3:
                    self.embed.title = response
                case 4:
                    self.embed.description = response
                case 5:
                    self.embed.url = response
                case 6:
                    try:
                        self.embed.color = discord.Color(int(response.replace("#", ""), 16))
                    except:
                        await self.send_step(interaction, "❌ Couleur invalide, utilisez un format #HEX.")
                        return await self.process_step(interaction)
                case 7:
                    if response.lower() == "oui":
                        self.current_step = 8  # Demander le nom du champ
                        return await self.process_step(interaction)
                    else:
                        self.current_step = 11  # Passer directement à l'image
                        return await self.process_step(interaction)
                case 8:
                    self.temp_field_name = response
                case 9:
                    self.embed.add_field(name=self.temp_field_name, value=response, inline=False)
                case 10:
                    if response.lower() == "oui":
                        self.current_step = 8  # Recommencer à ajouter un nouveau champ
                        return await self.process_step(interaction)
                    else:
                        self.current_step = 11  # Passer à l'étape image
                        return await self.process_step(interaction)
                case 11:
                    self.embed.set_image(url=response)
                case 12:
                    self.embed.set_thumbnail(url=response)
                case 13:
                    self.footer_text = response
                case 14:
                    self.embed.set_footer(
                        text=self.footer_text or discord.Embed.Empty,
                        icon_url=response
                    )
                case 15:
                    if response.lower() == "oui":
                        self.embed.timestamp = discord.utils.utcnow()
                case 16:
                    if response.lower() == "oui":
                        await interaction.channel.send(embed=self.embed)
                        await self.send_step(interaction, "✅ Embed envoyé.")
                        await send_log_message(interaction, f"{interaction.user} a créé et envoyé un embed")
                    else:
                        await self.send_step(interaction, "❌ Envoi annulé.")
                    self.stop()
                    return

        self.current_step += 1
        await self.update_embed_display(interaction)
        await self.process_step(interaction)

    @button(label="Suivant", style=discord.ButtonStyle.primary)
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.process_step(interaction)


class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @check_permissions("embed")
    @discord.app_commands.command(name="embed", description="Créer un embed personnalisable")
    async def embed_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        view = EmbedBuilder(self.bot)
        await interaction.followup.send("👷‍♂️ Vous allez créer un embed. Suivez les instructions.", ephemeral=True, view=view)


async def setup(bot):
    await bot.add_cog(EmbedCog(bot))
