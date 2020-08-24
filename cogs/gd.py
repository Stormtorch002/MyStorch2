from discord.ext import commands
import aiohttp


class GeometryDash(commands.Cog, name='Geometry Dash'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def level(self, ctx, level_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://gdbrowser.com/api/level/{level_id}') as resp:
                data = await resp.text()

        if data == '-1':
            return await ctx.send('nope')

        await ctx.send(data)


def setup(bot):
    bot.add_cog(GeometryDash(bot))
