from discord.ext import commands


class Counts(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.query = 'SELECT nickname, count, word FROM counts WHERE user_id = ? AND INSTR(?, word) > 0'

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        async with self.bot.db.cursor() as cur:
            await cur.execute(self.query, (message.author.id, message.content.lower(),))
            rows = await cur.fetchall()

            if rows:
                messages = []
                for row in rows:
                    messages.append(f'{row[0]} {row[2]} count: `{row[1] + 1}`')
                await message.channel.send('\n'.join(messages))
                query = 'UPDATE counts SET count = count + 1 WHERE word = ? AND user_id = ?'
                await cur.execute(query, (row[2], message.author.id))
                await self.bot.db.commit()

    @commands.command()
    async def addcount(self, ctx, nickname, *, word):
        async with self.bot.db.cursor() as cur:
            query = 'SELECT id FROM counts WHERE user_id = ? AND word = ?'
            await cur.execute(query, (ctx.author.id, word.lower()))
            exists = await cur.fetchone()

            if exists:
                return await ctx.send(f'You already have a {word} count.')

            query = 'INSERT INTO counts (user_id, nickname, count, word) VALUES (?, ?, ?, ?)'
            await cur.execute(query, (ctx.author.id, nickname, 0, word.lower()))
            await self.bot.db.commit()
            await ctx.send(f'Added your count.')


def setup(bot):
    bot.add_cog(Counts(bot))
