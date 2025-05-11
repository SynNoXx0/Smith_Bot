from discord.ext import commands, tasks
from utils.sheet_utils import get_all_worksheets
import asyncio

class GuildCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_guilds.start()

    def cog_unload(self):
        self.check_guilds.cancel()

    @tasks.loop(hours=168)  # une fois par semaine
    async def check_guilds(self):
        current_guild_ids = {str(guild.id) for guild in self.bot.guilds}
        worksheets = get_all_worksheets()

        for worksheet in worksheets:
            if worksheet.title == "access_levels":
                continue

            rows = worksheet.get_all_values()
            if not rows:
                continue

            headers = rows[0]
            data = rows[1:]

            if "guild_id" not in headers:
                continue

            guild_idx = headers.index("guild_id")
            rows_to_delete = []

            for i, row in enumerate(data, start=2):  # i = index réel dans Google Sheet
                if len(row) <= guild_idx:
                    continue
                if row[guild_idx] not in current_guild_ids:
                    rows_to_delete.append(i)

            for i in reversed(rows_to_delete):
                worksheet.delete_rows(i)

    @check_guilds.before_loop
    async def before_check_guilds(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(GuildCheck(bot))