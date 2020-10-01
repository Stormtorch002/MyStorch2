from discord.ext import commands
from config import TOKEN
import discord

bot = commands.Bot(
    command_prefix=['ms ', 'MS ', 'Ms '],
    case_insensitive=True,
    intents=discord.Intents.all()
)

bot.muted_role_id = 750144772559208599
bot.guild_id = 641379116007817216

for cog in (
    'on_ready',
    'moderation',
    'counting',
    'one_word_sentence',
    'suggestions',
    'tags',
    'npcs',
    'reaction_roles',
    'levels',
    'logs',
    'counts'
):
    bot.load_extension('cogs.' + cog)
bot.load_extension('jishaku')

bot.run(TOKEN)
