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
            },
            725166005596454913: {
                '\U0001f3d3': 727196155821162526,
                '\U0001f3b2': 727196148766474330,
                '\U0001f916': 727201028147249214,
                '\U0001f5e3': 727196147042615412
            },
            760847607253434449: {
                '\U0001f1e6': 753029940378861639,
                '\U0001f1e7': 753029946032783451,
                '\U0001f1e8': 753029946036715540,
                '\U0001f1e9': 753029946338836560,
                '\U0001f1ea': 753029947324497962,
                '\U0001f1eb': 753029951103696980
            }
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.reaction_roles:
            emoji = str(payload.emoji)
            reaction_role = self.reaction_roles[payload.message_id]
            if emoji in reaction_role:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(reaction_role[emoji])
                member = guild.get_member(payload.user_id)
                await member.add_roles(role)
                try:
                    await member.send(f'I have given you the `{role.name.split(" | ")[0]}` role!')
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in self.reaction_roles:
            emoji = str(payload.emoji)
            reaction_role = self.reaction_roles[payload.message_id]
            if emoji in reaction_role:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(reaction_role[emoji])
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)
                try:
                    await member.send(f'I have removed you from the `{role.name.split(" | ")[0]}` role!')
                except discord.Forbidden:
                    pass


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
