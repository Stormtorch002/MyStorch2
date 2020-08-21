from discord.ext import commands
import json


class Counting(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 728716336527704085

        with open('./cogs/counting.json') as f:
            data = json.load(f)

        self.data = data
        self.next = data['next']
        self.last_author_id = data['last_author_id']

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.channel.id == self.channel_id:

            if not message.content.isdigit() or int(message.content) != self.next or \
                    str(message.author.id) == self.last_author_id:
                await message.delete()
            else:
                self.next += 1
                self.last_author_id = self.data['last_author_id'] = str(message.author.id)
                self.data['next'] += 1

                with open('./cogs/counting.json', 'w') as f:
                    json.dump(self.data, f)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id == self.channel_id:
            await self.bot.http.delete_message(payload.channel_id, payload.message_id)


def setup(bot):
    bot.add_cog(Counting(bot))
