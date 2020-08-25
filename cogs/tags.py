from discord.ext import commands
from difflib import SequenceMatcher
import json
import discord
import time


def similarity(a, b):
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio


class Tags(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, tag_name):

        async with self.bot.db.cursor() as cur:
            query = 'SELECT response FROM tags WHERE name = ?'
            await cur.execute(query, (tag_name,))
            response = await cur.fetchone()

        if not response:
            similar = '\n'.join([f'`{name}`' for name in self.bot.tag_names if similarity(tag_name, name) > 0.7])
            if not similar:
                return await ctx.send('Tag not found.')
            else:
                return await ctx.send(f'Tag not found. Did you mean...\n\n{similar}')

        response = response[0]
        try:
            data = json.loads(response)
            embed = discord.Embed.from_dict(data)
            await ctx.send(embed=embed)
        except json.JSONDecodeError:
            await ctx.send(response)

        async with self.bot.db.cursor() as cur:
            query = 'UPDATE tags SET uses = uses + 1 WHERE name = ?'
            await cur.execute(query, (tag_name,))
            await self.bot.db.commit()

    @tag.command()
    async def add(self, ctx, name, *, response):
        async with self.bot.db.cursor() as cur:
            query = 'SELECT id FROM tags WHERE name = ?'
            await cur.execute(query, (name,))
            exists = await cur.fetchone()

            if exists:
                return await ctx.send(f'Tag `{name}` already exists.')

            query = 'INSERT INTO tags (name, response, creator_id, created_at, uses) VALUES (?, ?, ?, ?, ?)'
            await cur.execute(query, (name, response, ctx.author.id, int(time.time()), 0))
            await self.bot.db.commit()
        self.bot.tag_names.append(name)
        await ctx.send(f'Tag `{name}` created.')

    @tag.command()
    async def delete(self, ctx, *, name):
        async with self.bot.db.cursor() as cur:
            query = 'SELECT creator_id FROM tags WHERE name = ?'
            await cur.execute(query, (name,))
            exists = await cur.fetchone()

            if not exists:
                return await ctx.send(f'Tag `{name}` does not exist.')

            creator_id = exists[0]
            if ctx.author.id != creator_id and not ctx.author.guild_permissions.manage_guild:
                return await ctx.send('You are not authorized to delete this tag.')

            query = 'DELETE FROM tags WHERE name = ?'
            await cur.execute(query, (name,))
            await self.bot.db.commit()
        self.bot.tag_names.remove(name)
        await ctx.send(f'Delete tag `{name}`.')

    @tag.command()
    async def all(self, ctx):
        await ctx.send(' '.join([f'`{name}`' for name in self.bot.tag_names]))


def setup(bot):
    bot.add_cog(Tags(bot))
