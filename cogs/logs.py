from discord.ext import commands
import discord
from datetime import datetime


class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.join_role_ids = [
            728666908001566801,
            727195487580454912,
            725117486214938724,
            744608325001281566
        ]
        self.channel_id = 641433214631804959

    @commands.Cog.listener()
    async def on_member_join(self, member):
        roles = [self.bot.get_role(role_id) for role_id in self.join_role_ids]
        await member.add_roles(*roles)


def setup(bot):
    bot.add_cog(Logs(bot))
