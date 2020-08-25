from discord.ext import commands
import discord
import time
import parsedatetime
from cogs import menus
from datetime import datetime


def humanize(seconds: int):
    times = []
    y = seconds // 31536000
    seconds -= y * 31536000
    if y != 0:
        if y == 1:
            times.append(f'{y} year')
        else:
            times.append(f'{y} years')
    w = seconds // 604800
    seconds -= w * 604800
    if w != 0:
        if w == 1:
            times.append(f'{w} week')
        else:
            times.append(f'{w} weeks')
    d = seconds // 86400
    seconds -= d * 86400
    if d != 0:
        if d == 1:
            times.append(f'{d} day')
        else:
            times.append(f'{d} days')
    h = seconds // 3600
    seconds -= h * 3600
    if h != 0:
        if h == 1:
            times.append(f'{h} hour')
        else:
            times.append(f'{h} hours')
    m = seconds // 60
    seconds -= m * 60
    if m != 0:
        if m == 1:
            times.append(f'{m} minute')
        else:
            times.append(f'{m} minutes')
    if seconds != 0:
        if seconds == 1:
            times.append(f'{seconds} second')
        else:
            times.append(f'{seconds} seconds')

    return ', '.join(times)


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.parser = parsedatetime.Calendar()
        self.automod_query = 'SELECT word, punishment FROM swears WHERE INSTR(?, word) > 0 ORDER BY punishment DESC'
        self.ban_gif = 'https://media1.tenor.com/images/d856e0e0055af0d726ed9e472a3e9737/tenor.gif?itemid=8540509'
        self.mute_gif = 'https://thumbs.gfycat.com/UnfortunateGreatGavial-small.gif'

    def avatar(self, user):
        user = self.bot.get_user(user.id)
        fmt = 'png' if not user.is_avatar_animated() else 'gif'
        return str(user.avatar_url_as(format=fmt))

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        content = f' {message.content.lower()}  '
        async with self.bot.db.cursor() as cur:
            await cur.execute(self.automod_query, (content,))
            row = await cur.fetchone()

            if row:
                await message.delete()

                if row[1] == 1:
                    query = 'INSERT INTO warnings (user_id, mod_id, time, reason) VALUES (?, ?, ?, ?)'
                    await cur.execute(query,
                                      (message.author.id, self.bot.user.id, int(time.time()), f'saying {row[0]}'))
                    await self.bot.db.commit()
                    query = 'SELECT count(id) FROM warnings WHERE user_id = ?'
                    await cur.execute(query, (message.author.id,))
                    count = (await cur.fetchone())[0]

                    embed = discord.Embed(color=message.author.color)

                    if count == 3:
                        embed.set_thumbnail(url=self.mute_gif)
                        embed.set_author(name=f'Warning and Mute Issued', icon_url=self.avatar(message.author))
                        muted_role = self.bot.get_guild(self.bot.guild_id).get_role(self.bot.muted_role_id)
                        embed.description = f'**{message.author}** has been warned for saying ||{row[0]}||. ' \
                                            f'They now have `{count}` warnings **and will be muted for 12 hours.**'
                        await message.author.add_roles(muted_role)

                        query = 'INSERT INTO muted (user_id, muted_at, muted_until, reason) VALUES (?, ?, ?, ?)'
                        await cur.execute(query, (message.author.id, int(time.time()), int(time.time()) + 43200,
                                                  f'{count} warnings'))
                        await self.bot.db.commit()
                        embed.add_field(name='Unmute Time', value=datetime.fromtimestamp(int(time.time()) + 43200).
                                        strftime('%m/%d/%Y at %I:%M:%S %p EST'))
                    elif count == 5:
                        embed.set_thumbnail(url=self.ban_gif)
                        embed.set_author(name=f'Warning and Tempban Issued', icon_url=self.avatar(message.author))
                        embed.description = f'**{message.author} has been warned for saying ||{row[0]}||. ' \
                                            f'They now have `{count}` warnings **and will be tempbanned for 2 days.**'
                        embed.add_field(name='Unban Time', value=datetime.fromtimestamp(int(time.time()) + 172800).
                                        strftime('%m/%d/%Y at %I:%M:%S %p EST'))
                        await message.author.ban(reason=f'{count} warnings - 48h tempban')
                        query = 'INSERT INTO tempbanned (user_id, banned_at, banned_until, reason) VALUES (?, ?, ?, ?)'
                        await cur.execute(query, (message.author.id, int(time.time()), int(time.time()) + 172800,
                                                  f'{count} warnings'))
                        await self.bot.db.commit()
                    elif count == 6:
                        embed.set_thumbnail(url=self.ban_gif)
                        embed.set_thumbnail(url='')
                        embed.set_author(name=f'Warning and Ban Issued', icon_url=self.avatar(message.author))
                        embed.description = f'**{message.author}** has been warned for saying ||{row[0]}||. ' \
                                            f'They now have `{count}` warnings **and will be permanently banned.**'
                        await message.author.ban(reason=f'{count} warnings')
                    else:
                        embed.set_author(name=f'Warning Issued', icon_url=self.avatar(message.author))
                        embed.description = f'**{message.author}** has been warned for saying ||{row[0]}||. ' \
                                            f'They now have `{count}` warnings.'
                    await message.channel.send(embed=embed)
                else:
                    await message.author.ban(reason='n word')

    @commands.command()
    @commands.has_any_role(725117477578866798, 725117459803275306, 725117475368206377, 725117475997483126)
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
            embed.add_field(name='Unmute Time', value=datetime.fromtimestamp(int(time.time()) + 43200).
                            strftime('%m/%d/%Y at %I:%M:%S %p EST'))
        elif count == 5:
            embed.description = f'**{member}** now has `{count}` warnings. **They will be tempbanned for 2 days.**'
            embed.add_field(name='Unban Time', value=datetime.fromtimestamp(int(time.time()) + 172800).
                            strftime('%m/%d/%Y at %I:%M:%S %p EST'))
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
    @commands.has_any_role(725117459803275306, 725117475368206377, 725117475997483126)
    async def clearwarn(self, ctx, warning_ids: commands.Greedy[int]):

        async with self.bot.db.cursor() as cur:
            for warning_id in warning_ids:
                query = 'DELETE FROM warnings WHERE id = ?'
                await cur.execute(query, (warning_id,))
                await self.bot.db.commit()

        await ctx.send(f'Cleared warnings.')

    @commands.group(invoke_without_command=True)
    @commands.has_any_role(725117477578866798, 725117459803275306, 725117475368206377, 725117475997483126)
    async def warnings(self, ctx):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT id, user_id, mod_id, reason, time FROM warnings'
            await cur.execute(query)
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)

    @warnings.command(name='for')
    @commands.has_any_role(725117477578866798, 725117459803275306, 725117475368206377, 725117475997483126)
    async def _for(self, ctx, *, member: discord.Member):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT id, user_id, mod_id, reason, time FROM warnings WHERE user_id = ?'
            await cur.execute(query, (member.id,))
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)

    @warnings.command()
    @commands.has_any_role(725117477578866798, 725117459803275306, 725117475368206377, 725117475997483126)
    async def done(self, ctx, *, member: discord.Member):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT user_id, mod_id, reason, time FROM warnings WHERE mod_id = ?'
            await cur.execute(query, (member.id,))
            ctx.rows = await cur.fetchall()

            if not ctx.rows:
                return await ctx.send('No warnings found.')

        await menus.WarningsMenu().start(ctx)

    @commands.command()
    @commands.has_any_role(725117477578866798, 725117459803275306, 725117475368206377, 725117475997483126)
    async def mute(self, ctx, member: discord.Member, *, time_reason):

        if self.bot.muted_role_id in [role.id for role in member.roles]:
            return await ctx.send(f'{member} is already muted.')

        parsed = self.parser.parse(time_reason)[0]

        mute_time = int(time.mktime(parsed))
        mute_length = mute_time - int(time.time())
        reason = ' '.join([word for word in time_reason.split() if not (word[0].isdigit() and not word[1].isdigit())])

        if reason.isspace():
            reason = 'None'

        role = ctx.guild.get_role(self.bot.muted_role_id)
        await member.add_roles(role, reason=reason)

        async with self.bot.db.cursor() as cur:
            query = 'INSERT INTO muted (user_id, muted_at, muted_until, reason) VALUES (?, ?, ?, ?)'
            await cur.execute(query, (member.id, int(time.time()), mute_time, reason))
            await self.bot.db.commit()

        embed = discord.Embed(color=member.color)
        embed.set_author(name=f'{member} was Muted', icon_url=self.avatar(member))
        embed.add_field(name='User', value=member.mention)
        embed.add_field(name='Moderator', value=ctx.author.mention)
        embed.add_field(name='Mute Length', value=humanize(mute_length))
        embed.add_field(name='Unmute Time',
                        value=datetime.fromtimestamp(mute_time).strftime('%m/%d/%Y at %I:%M:%S %p EST'))
        embed.add_field(name='Reason', value=reason)
        print(embed.fields[2].value)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role(725117459803275306, 725117475368206377, 725117475997483126)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)

    @commands.command()
    @commands.has_any_role(725117459803275306, 725117475368206377, 725117475997483126)
    async def slowmode(self, ctx, channel: discord.TextChannel, delay: float):
        await channel.edit(slowmode_delay=delay)
        await ctx.send('Done')


def setup(bot):
    bot.add_cog(Moderation(bot))
