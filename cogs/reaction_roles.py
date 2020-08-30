from discord.ext import commands
import discord


class ReactionRoles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {
            725166011115896923: {
                '\U0001f4e3': 728665957597315102,
                '\U0001f389': 728666898597937163,
                '\U0001f4b0': 728666869086683197,
                '\U0001f3df': 728666439623376908
            }
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.reaction_roles.keys():
            emoji = str(payload.emoji)
            reaction_role = self.reaction_roles[payload.message_id]
            if emoji in reaction_role.keys():
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(reaction_role[emoji])
                member = guild.get_member(payload.user_id)
                await member.add_roles(role)
                try:
                    await member.send(f'I have given you the `{role.name}` role!')
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in self.reaction_roles.keys():
            emoji = str(payload.emoji)
            reaction_role = self.reaction_roles[payload.message_id]
            if emoji in reaction_role.keys():
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(reaction_role[emoji])
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)
                try:
                    await member.send(f'I have removed you from the `{role.name}` role!')
                except discord.Forbidden:
                    pass


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
