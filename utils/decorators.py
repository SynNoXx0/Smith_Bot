import discord
from discord import app_commands
from discord import Interaction
from utils.sheet_utils import is_role_allowed_for_command
from utils.sheet_utils import get_guild_grade

def check_permissions(command_name: str):
    async def predicate(interaction: Interaction):
        # Si l'utilisateur a les permissions admin, autorisé
        if interaction.user.guild_permissions.administrator:
            return True

        # Sinon on vérifie les rôles
        user_role_ids = [role.id for role in interaction.user.roles]
        if is_role_allowed_for_command(str(interaction.guild.id), command_name, user_role_ids):
            return True

        # Sinon, on refuse
        raise app_commands.CheckFailure("Tu n'as pas la permission d'utiliser cette commande.")
    return app_commands.check(predicate)

def check_public_permissions(command_name: str):
    async def predicate(interaction: Interaction):
        # Récupérer les rôles de l'utilisateur
        user_role_ids = [role.id for role in interaction.user.roles]
        
        # Vérifier si l'utilisateur a un rôle autorisé pour la commande
        if is_role_allowed_for_command(str(interaction.guild.id), command_name, user_role_ids):
            return True

        # Sinon, on refuse
        raise app_commands.CheckFailure("Tu n'as pas la permission d'utiliser cette commande.")

    return app_commands.check(predicate)

def require_grade(*allowed_grades):
    def decorator(func):
        async def wrapper(self, interaction, *args, **kwargs):
            grade = get_guild_grade(interaction.guild.id)
            if grade in allowed_grades:
                return await func(self, interaction, *args, **kwargs)
            await interaction.response.send_message(
                "Ce serveur n'est pas autorisé à utiliser cette commande.", ephemeral=True
            )
        return wrapper
    return decorator