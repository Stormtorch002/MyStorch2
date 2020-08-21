from discord.ext import commands
import discord
import time
import typing
from cogs import menus


def is_staff(ctx):
    return 692910121776447528 in [role.id for role in ctx.author.roles]


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def avatar(self, user):
        user = self.bot.get_user(user.id)
        fmt = 'png' if not user.is_avatar_animated() else 'gif'
        return str(user.avatar_url_as(format=fmt))

    @commands.command()
    @commands.check(is_staff)
    async def warn(self, ctx, member: discord.Member, *, reason):
        muted_role = self.bot.get_guild(self.bot.guild_id).get_role(self.bot.muted_role_id)

        async with self.bot.db.cursor() as cur:
            query = 'INSERT INTO warnings (user_id, mod_id, reason, time) VALUES (?, ?, ?, ?)'
            await cur.execute(query, (member.id, ctx.author.id, reason, int(time.time())))
            await self.bot.db.commit()

            query = 'SELECT COUNT(id) FROM warnings WHERE user_id = ?'
            await cur.execute(query, (member.id,))
            count = (await cur.fetchone())[0]

        embed = discord.Embed(color=discord.Colour.red())

        if count == 3:
            embed.description = f'**{member}** now has `{count}` warnings. **They will be muted for 12 hours.**'
            await member.add_roles(muted_role)

            async with self.bot.db.cursor() as cur:
                query = 'INSERT INTO muted (user_id, muted_at, muted_until, reason) VALUES (?, ?, ?, ?)'
                await cur.execute(query, (member.id, int(time.time()), int(time.time()) + 43200, f'{count} warnings'))
                await self.bot.db.commit()
        elif count == 5:
            embed.description = f'**{member}** now has `{count}` warnings. **They will be tempbanned for 2 days.**'
            await member.ban(reason=f'{count} warnings - 48h tempban')

            async with self.bot.db.cursor() as cur:
                query = 'INSERT INTO tempbanned (user_id, banned_at, banned_until, reason) VALUES (?, ?, ?, ?)'
                await cur.execute(query, (member.id, int(time.time()), int(time.time()) + 172800, f'{count} warnings'))
                await self.bot.db.commit()
        elif count == 6:
            embed.description = f'**{member}** now has `{count}` warnings. **They will be permanently banned.**'
            await member.ban(reason=f'{count} warnings')

        embed.add_field(name='User', value=member.mention)
        embed.add_field(name='Moderator', value=ctx.author.mention)
        embed.add_field(name='Reason', value=reason)
        embed.set_author(name=f'Warning Issued', icon_url=self.avatar(member))
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(is_staff)
    async def clearwarn(self, ctx, *, warning_ids: commands.Greedy[int]):

        async with self.bot.db.cursor() as cur:
            for warning_id in warning_ids:
                query = 'DELETE FROM warnings WHERE id = ?'
                await cur.execute(query, (warning_id,))
        await ctx.send(f'Cleared warnings.')

    @commands.group()
    @commands.check(is_staff)
    async def warnings(self, ctx):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT id, user_id, mod_id, reason, time FROM warnings'
            await cur.execute(query)
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)

    @warnings.command(name='for')
    async def _for(self, ctx, *, member: discord.Member):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT id, user_id, mod_id, reason, time FROM warnings WHERE user_id = ?'
            await cur.execute(query, (member.id,))
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)

    @warnings.command()
    async def done(self, ctx, *, member: discord.Member):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT user_id, mod_id, reason, time FROM warnings WHERE mod_id = ?'
            await cur.execute(query, (member.id,))
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)


def setup(bot):
    bot.add_cog(Moderation(bot))
