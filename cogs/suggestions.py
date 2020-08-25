from discord.ext import commands
import time


class Suggestions(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def avatar(self, user):
        user = self.bot.get_user(user.id)
        fmt = 'png' if not user.is_avatar_animated() else 'gif'
        return str(user.avatar_url_as(format=fmt))

    @commands.command(hidden=True)  # revamp isn't done yet lol
    async def suggest(self, ctx, *, suggestion):
        return await ctx.send('hey yo the revamp isnt done yet')  # will remove this after revamp

        async with self.bot.db.cursor() as cur:
            query = 'SELECT reset_time FROM suggestion_cooldowns WHERE user_id = ?'
            await cur.execute(query, (ctx.author.id, time.time()))
            reset_time = await cur.fetchone()

            if reset_time:
                if reset_time[0] < time.time():
                    x = True
                    await cur.execute('DELETE FROM suggeston_cooldowns WHERE user_id = ?')
                    await self.bot.db.commit()
                else:
                    x = False
            else:
                x = True

        if not x:
            return await ctx.send(f'You can only post a suggestion once every **12 hours.**')

        channel = bot.get_channel(726577000881586288)
        embed = discord.Embed(color=ctx.author.color, descirption=suggestion)
        embed.set_author(name=f'Suggestion from {ctx.author}', icon_url=self.avatar(ctx.author))
        message = await channel.send(embed=embed)

        for emoji in ('\U0001f44d', '\U0001f44e'):
            await message.add_reaction(emoji)

        async with self.bot.db.cursor() as cur:
            query = 'INSERT INTO suggestion_cooldowns (user_id, reset_time) VALUES (?, ?)'
            await cur.execute(query, (ctx.author.id, int(time.time() + 43200)))
            await self.bot.db.commit()

        await ctx.send(f'Thanks for your suggestion! You can view it in {channel.mention}')


def setup(bot):
    bot.add_cog(Suggestions(bot))
