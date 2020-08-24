from discord.ext import menus
import discord
from datetime import datetime


def create_embed(bot, queried_rows, page):
    chunks = [queried_rows[x:x + 5] for x in range(0, len(queried_rows), 5)]
    chunk = chunks[page - 1]

    guild = bot.get_guild(bot.guild_id)
    desc = '```ID: {}\nUSER: {}\nMOD: {}\nREASON: {}\nTIME: {}```'
    desc = '\n'.join([desc.format(warn[0], guild.get_member(warn[1]), guild.get_member(warn[2]),
                                  warn[3], datetime.fromtimestamp(warn[4]).strftime("%m/%d/%Y at %I:%M:%S %p EST"))
                      for warn in chunk])
    embed = discord.Embed(color=discord.Colour.blue())
    embed.title = f'{len(queried_rows)} Warnings'
    embed.description = desc
    embed.set_author(name=f'Page {page}/{len(chunks)}')
    return embed


class WarningsMenu(menus.Menu):

    def __init__(self, *, timeout=180.0, delete_message_after=False,
                 clear_reactions_after=False, check_embeds=False, message=None):
        super().__init__(timeout=180.0, delete_message_after=False, clear_reactions_after=False, check_embeds=False,
                         message=None)
        self.page = 1
        self.rows = []

    async def send_initial_message(self, ctx, channel):
        rows = ctx.rows
        self.rows = rows
        embed = create_embed(self.bot, self.rows, 1)
        return await ctx.send(embed=embed)

    @menus.button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}')
    async def on_first(self, payload):
        if self.page != 1:
            embed = create_embed(self.bot, self.rows, 1)
            self.page = 1
            await self.message.edit(embed=embed)

    @menus.button('\N{BLACK LEFT-POINTING TRIANGLE}')
    async def on_left(self, payload):
        if self.page != 1:
            embed = create_embed(self.bot, self.rows, self.page - 1)
            self.page -= 1
            await self.message.edit(embed=embed)

    @menus.button('\N{BLACK RIGHT-POINTING TRIANGLE}')
    async def on_right(self, payload):
        if self.page != len(self.rows):
            embed = create_embed(self.bot, self.rows, self.page + 1)
            self.page += 1
            await self.message.edit(embed=embed)

    @menus.button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}')
    async def on_last(self, payload):
        if self.page != len(self.rows):
            embed = create_embed(self.bot, self.rows, len(self.rows))
            self.page = len(self.rows)
            await self.message.edit(embed=embed)
