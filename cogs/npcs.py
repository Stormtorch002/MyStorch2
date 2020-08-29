from discord.ext import commands
import aiohttp
import discord


class NPCs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.webhook_urls = {
            645336386680913920: 'https://discord.com/api/webhooks/749276137649078382/'
                                'DrCTukhN8uXk2mhSEnUNIDbh3O9rgsCrNl_GOH80ULQdS0v5sr4Ki-s0Yi63ZE9mbqWi'
        }
        self.allowed_channels = self.webhook_urls.keys()

    @commands.group(invoke_without_command=True)
    async def npc(self, ctx, alias, *, message):

        if ctx.channel.id not in self.allowed_channels:
            return await ctx.send('You cannot use NPCs here.')
        if alias not in self.bot.npc_aliases:
            return await ctx.send('NPC not found.')

        async with self.bot.db.cursor() as cur:
            query = 'SELECT name, avatar_url, granted FROM npcs WHERE alias = ?'
            await cur.execute(query, (alias,))
            row = await cur.fetchone()

        if str(ctx.author.id) not in row[2].split() and not ctx.author.guild_permissions.administrator:
            return await ctx.send(f'You are not authorized to use this NPC.')

        data = {
            "content": message,
            "username": row[0],
        }
        if row[1]:
            data['avatar_url'] = row[1]

        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_urls[ctx.channel.id], data=data)
            await ctx.message.delete()

    @npc.command()
    async def add(self, ctx, alias, name, avatar_url=''):
        if alias in self.bot.npc_aliases:
            return await ctx.send(f'NPC with alias `{alias}` already exists.')

        async with self.bot.db.cursor() as cur:
            query = 'INSERT INTO npcs (alias, name, granted, avatar_url, creator_id) VALUES (?, ?, ?, ?, ?)'
            await cur.execute(query, (alias, name, str(ctx.author.id), avatar_url, ctx.author.id))
            await self.bot.db.commit()
            self.bot.npc_aliases.append(alias)

        await ctx.send('NPC added!')

    @npc.command()
    async def grant(self, ctx, alias, *, member: discord.Member):
        if alias not in self.bot.npc_aliases:
            return await ctx.send(f'Alias `{alias}` not found.')

        async with self.bot.db.cursor() as cur:
            query = 'SELECT granted, creator_id FROM npcs WHERE alias = ?'
            await cur.execute(query, (alias,))
            row = await cur.fetchone()

            if ctx.author.id != row[1] and not ctx.author.guild_permissions.administrator:
                return await ctx.send('You are not authorized to grant this NPC.')
            if str(member.id) in row[0].split() or member.guild_permissions.administrator:
                return await ctx.send(f'`{member}` already is granted to this NPC.')

            granted = row[0] + f' {member.id}'
            query = 'UPDATE npcs SET granted = ? WHERE alias = ?'
            await cur.execute(query, (granted, alias))
            await self.bot.db.commit()

            await ctx.send(f'Granted the NPC to `{member}`.')


def setup(bot):
    bot.add_cog(NPCs(bot))
