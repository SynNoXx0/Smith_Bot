import random
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from utils.decorators import check_permissions, check_public_permissions
from cogs.logs import send_log_message

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /say
    @check_permissions("say")
    @app_commands.command(name="say", description="Faire parler le bot dans le salon.")
    @app_commands.describe(message="Message que le bot doit envoyer")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Message envoyé.", ephemeral=True)
        await send_log_message(interaction, f"{interaction.user} a fait parler le bot : {message}")

    # /coinflip
    @check_public_permissions("coinflip")
    @app_commands.command(name="coinflip", description="Pile ou face")
    async def coinflip(self, interaction: Interaction):
        result = random.choice(["🪙 Pile", "🪙 Face"])
        await interaction.response.send_message(f"Résultat : **{result}**")
        await send_log_message(interaction, f"{interaction.user} a lancé une pièce : {result}")

    # /dice
    @check_public_permissions("dice")
    @app_commands.command(name="dice", description="Lance un dé à 6 faces")
    async def dice(self, interaction: Interaction):
        result = random.randint(1, 6)
        await interaction.response.send_message(f"🎲 Tu as lancé un dé : **{result}**")
        await send_log_message(interaction, f"{interaction.user} a lancé un dé : {result}")

    # /chifumi
    @check_public_permissions("chifumi")
    @app_commands.command(name="chifumi", description="Joue à pierre-feuille-ciseaux contre le bot")
    @app_commands.describe(choice="Ton choix : pierre, feuille ou ciseaux")
    async def chifumi(self, interaction: Interaction, choice: str):
        choix_user = choice.lower()
        if choix_user not in ["pierre", "feuille", "ciseaux"]:
            await interaction.response.send_message("❌ Choix invalide. Choisis entre `pierre`, `feuille` ou `ciseaux`.")
            return

        choix_bot = random.choice(["pierre", "feuille", "ciseaux"])
        resultat = {
            ("pierre", "ciseaux"): "Tu gagnes !",
            ("feuille", "pierre"): "Tu gagnes !",
            ("ciseaux", "feuille"): "Tu gagnes !",
        }

        if choix_user == choix_bot:
            msg = "Égalité !"
        else:
            msg = resultat.get((choix_user, choix_bot), "Tu perds !")

        await interaction.response.send_message(f"🤖 Le bot a choisi **{choix_bot}**.\nRésultat : **{msg}**")
        await send_log_message(interaction, f"{interaction.user} a joué à chifumi : {choix_user} vs {choix_bot} - {msg}")

    # /tictactoe
    @check_public_permissions("tictactoe")
    @app_commands.command(name="tictactoe", description="Joue à un jeu de morpion contre quelqu'un.")
    @app_commands.describe(adversaire="Mentionne l'utilisateur contre qui tu veux jouer")
    async def tictactoe(self, interaction: discord.Interaction, adversaire: discord.Member):
        if adversaire.bot:
            await interaction.response.send_message("Tu ne peux pas jouer contre un bot.", ephemeral=True)
            return
        if adversaire == interaction.user:
            await interaction.response.send_message("Tu ne peux pas jouer contre toi-même.", ephemeral=True)
            return

        view = TicTacToeView(interaction.user, adversaire)
        await interaction.response.send_message(
            f"{interaction.user.mention} VS {adversaire.mention}\nC'est au tour de {interaction.user.mention}",
            view=view
        )
        await send_log_message(interaction, f"{interaction.user} a lancé une partie de morpion contre {adversaire}")

class TicTacToeButton(discord.ui.Button):
    def __init__(self, row, col):
        super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=row)
        self.row = row
        self.col = col

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user != view.current_player:
            await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
            return

        if view.board[self.row][self.col] != "":
            await interaction.response.send_message("Cette case est déjà prise !", ephemeral=True)
            return

        symbol = "❌" if view.current_player == view.player1 else "⭕"
        self.label = symbol
        self.disabled = True
        self.style = discord.ButtonStyle.success if symbol == "❌" else discord.ButtonStyle.danger
        view.board[self.row][self.col] = symbol
        winner = view.check_winner()

        if winner:
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(content=f"{interaction.user.mention} a gagné ! 🎉", view=view)
            await send_log_message(interaction, f"Partie de morpion terminée : {interaction.user} a gagné contre {view.player2 if interaction.user == view.player1 else view.player1}")
            view.stop()
        elif view.is_full():
            await interaction.response.edit_message(content="Match nul ! 🤝", view=view)
            await send_log_message(interaction, f"Partie de morpion terminée : Match nul entre {view.player1} et {view.player2}")
            view.stop()
        else:
            view.current_player = view.player2 if view.current_player == view.player1 else view.player1
            await interaction.response.edit_message(content=f"C'est au tour de {view.current_player.mention}", view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [["" for _ in range(3)] for _ in range(3)]

        for row in range(3):
            for col in range(3):
                self.add_item(TicTacToeButton(row, col))

    def check_winner(self):
        for row in self.board:
            if row[0] and row[0] == row[1] == row[2]:
                return row[0]

        for col in range(3):
            if self.board[0][col] and self.board[0][col] == self.board[1][col] == self.board[2][col]:
                return self.board[0][col]

        if self.board[0][0] and self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return self.board[0][0]
        if self.board[0][2] and self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return self.board[0][2]

        return None

    def is_full(self):
        return all(cell != "" for row in self.board for cell in row)

async def setup(bot):
    await bot.add_cog(Fun(bot))