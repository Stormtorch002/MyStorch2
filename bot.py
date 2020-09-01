from discord.ext import commands
from config import TOKEN

bot = commands.Bot(command_prefix=commands.when_mentioned_or('ms '))
bot.muted_role_id = 750144772559208599
bot.guild_id = 641379116007817216

for cog in (
    'on_ready',
    'moderation',
    'counting',
    'one_word_sentence',
    'gd',
    'suggestions',
    'tags',
    'npcs',
    'reaction_roles',
    'levels',
    'logs'
):
    bot.load_extension('cogs.' + cog)
bot.load_extension('jishaku')

bot.run(TOKEN)
