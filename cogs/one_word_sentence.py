from discord.ext import commands
import json


class OneWordSentence(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 728722955013718037

        with open('./cogs/one_word_sentence.json') as f:
            data = json.load(f)

        self.data = data
        self.last_author_id = data['last_author_id']

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.channel.id == self.channel_id:
            if not message.content.isalpha() or str(message.author.id) == self.last_author_id:
                await message.delete()
            else:
                self.last_author_id = self.data['last_author_id'] = str(message.author.id)

                with open('./cogs/one_word_sentence.json', 'w') as f:
                    json.dump(self.data, f, indent=2)


def setup(bot):
    bot.add_cog(OneWordSentence(bot))
