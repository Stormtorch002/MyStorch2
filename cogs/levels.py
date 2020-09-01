from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw, ImageOps, ImageEnhance
from io import BytesIO
from colour import Color
import time
import random
import discord
import aiohttp
import math


def bordered_text(draw: ImageDraw.ImageDraw, xy: tuple, text, font: ImageFont, fill: tuple, outline: tuple,
                  thiccness: int):
    x, y = xy[0], xy[1]
    draw.text((x - thiccness, y - thiccness), text, font=font, fill=outline)
    draw.text((x + thiccness, y - thiccness), text, font=font, fill=outline)
    draw.text((x - thiccness, y + thiccness), text, font=font, fill=outline)
    draw.text((x + thiccness, y + thiccness), text, font=font, fill=outline)
    draw.text(xy=(x, y), text=text, fill=fill, font=font)


def get_xp(lvl: int):
    xp = 21 * lvl * (lvl - 1)
    return xp


def get_level(xp: int):
    lvl = int((1 + math.sqrt(1 + 8 * xp / 42)) / 2)
    return lvl


class Levels(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.disabled_channels = (
            725095850446946344,
            728659433541861476,
            728659470150008913,
            725164675679125515,
            728716336527704085,
            728717757490921603,
            728722955013718037,
            730486347474796544,
            740227585014759444,
            743855545697566750,
            743881454068695041
        )
        self.leveled_roles = {
            1: 726131163743256596,
            2: 726131155664896046,
            4: 726131162862583828,
            6: 726131148480053339,
            8: 725460673953529936,
            10: 725136991951519774,
            12: 725117516887621703,
            14: 725117516493357087,
            16: 725117514043883550,
            18: 725117513821716481,
            20: 725117511414186005,
            22: 725117508939677746,
            24: 725117506439610390,
            26: 725117506401861693,
            28: 725117503491014789,
            30: 725117501545119784,
            35: 725117500966043659,
            40: 725117498491404353,
            45: 725117496255840306,
            50: 725117495958175815,
            55: 725117493990916137,
            60: 725117491621265479,
            65: 725117491373801570,
            70: 725117488693641276
        }
        self.xp_cooldowns = {}
        self.zerotwo = 'https://media.discordapp.net/attachments/597045636063559690/750124811358961776/do-sharp.png'

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in self.disabled_channels and not message.author.bot:
            if message.author.id not in self.xp_cooldowns or self.xp_cooldowns[message.author.id] < time.time():
                if message.author.id not in self.bot.leveling:
                    self.bot.leveling[message.author.id] = 0

                    async with self.bot.db.cursor() as cur:
                        query = 'INSERT INTO leveling (user_id, xp, color, url) VALUES (?, ?, ?, ?)'
                        await cur.execute(query, (message.author.id, 0, '#7289DA', self.zerotwo))
                        await self.bot.db.commit()
                else:
                    old_level = get_level(self.bot.leveling[message.author.id])
                    increment = random.randint(3, 7)
                    self.bot.leveling[message.author.id] += increment
                    new_level = get_level(self.bot.leveling[message.author.id])

                    authorroles = [role.id for role in message.author.roles]
                    role = [self.leveled_roles[lvl] for lvl in self.leveled_roles.keys() if lvl <= new_level]
                    if role:
                        role = role[-1]
                        if role not in authorroles:
                            role = message.guild.get_role(role)
                            await message.author.add_roles(role)

                    async with self.bot.db.cursor() as cur:
                        query = 'UPDATE leveling SET xp = xp + ? WHERE user_id = ?'
                        await cur.execute(query, (increment, message.author.id,))
                        await self.bot.db.commit()

                    if old_level != new_level:
                        await message.channel.send(
                            f'Congrats, {message.author.mention}! You made it to level **{new_level}**.')
                        self.xp_cooldowns[message.author.id] = time.time() + 15

    @commands.group(name='rank', invoke_without_command=True)
    async def _rank(self, ctx, *, mem: discord.Member = None):
        m = mem if mem else ctx.author

        try:
            xp = self.bot.leveling[m.id]
        except KeyError:
            return await ctx.send(f"`{m}` isn't enlisted in the server level system yet.")

        rank = sorted([self.bot.leveling[user] for user in self.bot.leveling.keys()], reverse=True).index(xp) + 1

        message = await ctx.send('processing image... ~~y python so slow~~')
        start = time.time()

        async with self.bot.db.cursor() as cur:
            query = 'SELECT color, url FROM leveling WHERE user_id = ?'
            await cur.execute(query, (m.id,))
            row = await cur.fetchone()
            color, url = row[0], row[1]

        if url == 'https://media.discordapp.net/attachments/597045636063559690/750124811358961776/do-sharp.png':
            tip = 'TIP: You can do `ms rank image <image url>` to change your rank card image!'
        else:
            tip = ''

        mx = xp
        current_level = get_level(mx)
        nlr = nl = None

        for l in self.leveled_roles.keys():
            if l > current_level:
                nlr = ctx.guild.get_role(self.leveled_roles[l])
                nl = l
                break

        next_level = current_level + 1
        current_level_xp, next_level_xp = get_xp(current_level), get_xp(next_level)
        progress, total_xp = mx - current_level_xp, next_level_xp - current_level_xp
        ratio = progress / total_xp

        avatar_data = await m.avatar_url.read()

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    image_data = await resp.read()
                async with session.get(str(m.avatar_url_as(format='png'))) as resp:
                    avatar_data = await resp.read()
            except aiohttp.InvalidURL:
                await message.edit(content='The image URL you set for your rank card was not valid.')
                return

        def process_image():
            # open
            with \
                    Image.open('./cogs/images/template.png') as template, \
                    Image.open(BytesIO(avatar_data)) as av, \
                    Image.open('./cogs/images/border.png') as border, \
                    Image.open(BytesIO(image_data)) as image:

                # resize
                border = border.resize(size=(235, 235))
                size = image.size
                multiplier = 900 / size[0]
                image = image.resize(size=(900, int(size[1] * multiplier)))
                image = ImageOps.fit(image, size=(900, 240))
                # darken
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(0.5)
                template.paste(image, (20, 25))
                x = int(365 * ratio) + 355

                if m.color == discord.Color.default():
                    c = (255, 255, 255)
                else:
                    c = m.color.to_rgb()

                avatar_size = int(template.size[1] * 2 / 3)
                av = av.resize((avatar_size, avatar_size))
                av = av.convert(mode='RGBA')

                im_a = Image.new("L", av.size, 0)
                draw = ImageDraw.Draw(im_a)
                draw.ellipse([(0, 0), av.size], fill=255)
                template.paste(av, (40, 45), im_a)
                draw = ImageDraw.Draw(template, mode='RGBA')
                draw.rectangle([(355, 175), (720, 200)], fill=(169, 169, 169, 255), outline=(0, 0, 0, 255))
                draw.rectangle([(355, 175), (x, 200)], fill=color, outline=(0, 0, 0, 255))
                font = ImageFont.truetype('./cogs/fonts/mono.ttf', 38)
                size = font.getsize(str(current_level))[0]
                x = 330 - size
                draw.text(xy=(x, 170), font=font, fill=(255, 255, 255, 255), text=str(current_level))
                draw.text(xy=(745, 170), font=font, fill=(255, 255, 255, 255), text=str(current_level + 1))
                font = ImageFont.truetype('./cogs/fonts/ubuntu.ttf', 38)
                bordered_text(draw=draw, font=font, xy=(300, 110), text=f'Rank: ', fill=(255, 255, 255, 255),
                              outline=(0, 0, 0, 255), thiccness=2)
                textlen = font.getsize("Rank: ")[0]
                font = ImageFont.truetype('./cogs/fonts/mono.ttf', 48)
                bordered_text(xy=(410, 107), draw=draw, text=str(rank), font=font, fill=color, thiccness=2,
                              outline=(0, 0, 0, 255))
                ranklen = font.getsize(str(rank))[0]
                totallen = textlen + ranklen + 315

                if len(m.display_name) > 12:

                    if len(m.display_name) > 17:
                        text = m.display_name[:16]
                    else:
                        text = m.display_name

                    font = ImageFont.truetype('./cogs/fonts/ubuntu.ttf', 36)
                    bordered_text(draw=draw, xy=(300, 50), text=text, font=font, fill=(c[0], c[1], c[2], 255),
                                  outline=(0, 0, 0, 255), thiccness=1)
                else:
                    font = ImageFont.truetype('./cogs/fonts/ubuntu.ttf', 45)
                    text = m.display_name
                    bordered_text(draw=draw, xy=(300, 55), text=text, font=font, fill=(c[0], c[1], c[2], 255),
                                  outline=(0, 0, 0, 255), thiccness=1)

                x = font.getsize(text)[0] + 315

                if x < totallen:
                    x = totallen + 5

                draw.rectangle(xy=[(x, 55), (x + 5, 150)], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
                font = ImageFont.truetype('./cogs/fonts/ubuntu.ttf', 32)
                bordered_text(xy=(x + 30, 65), draw=draw, font=font, text='LEVEL', fill=(255, 255, 255, 255),
                              thiccness=2, outline=(0, 0, 0, 255))
                bordered_text(xy=(x + 30, 115), draw=draw, font=font, text='TOTAL XP:', fill=(255, 255, 255, 255),
                              thiccness=2,
                              outline=(0, 0, 0, 255))
                font = ImageFont.truetype('./cogs/fonts/mono.ttf', 62)
                bordered_text(xy=(x + 130, 47), font=font, draw=draw, text=str(current_level), thiccness=2,
                              outline=(0, 0, 0, 255), fill=color)
                font = ImageFont.truetype('./cogs/fonts/mono.ttf', 42)

                if mx > 999:
                    member_xp = f'{round(mx / 1000, 1)}K'
                else:
                    member_xp = str(mx)

                bordered_text(xy=(x + 190, 112), font=font, draw=draw, text=member_xp, thiccness=2,
                              outline=(0, 0, 0, 255), fill=color)

                if nlr:
                    role_color = nlr.color.to_rgb()
                    color_tuple = (role_color[0], role_color[1], role_color[2], 255)
                    role_name = nlr.name.split(' | ')[0]
                    levels_to = nl - current_level

                    if levels_to == 1:
                        s = ''
                    else:
                        s = 's'

                    font = ImageFont.truetype('./cogs/fonts/mono.ttf', 35)
                    text = f'{progress}/{total_xp}'
                    bordered_text(draw=draw, font=font, thiccness=1, text=text, fill=color,
                                  outline=(0, 0, 0, 255), xy=(260, 220))
                    size = font.getsize(text)[0]
                    text = f' XP | {levels_to} Level{s} to '
                    font = ImageFont.truetype("./cogs/fonts/ubuntu.ttf", 30)
                    bordered_text(draw=draw, font=font, thiccness=1, text=text, fill=(255, 255, 255, 255),
                                  outline=(0, 0, 0, 255), xy=(260 + size, 220))
                    text_length = font.getsize(text)[0]
                    bordered_text(draw=draw, font=font, thiccness=1, text=role_name, fill=color_tuple,
                                  outline=(0, 0, 0, 255), xy=(260 + size + text_length, 220))
                else:
                    font = ImageFont.truetype('./cogs/fonts/mono.ttf', 35)
                    text = f'{progress}/{total_xp}'
                    bordered_text(draw=draw, font=font, thiccness=1, text=text, fill=color,
                                  outline=(0, 0, 0, 255), xy=(300, 220))
                    size = font.getsize(text)[0]
                    text = ' XP to Next Level'
                    font = ImageFont.truetype("./cogs/fonts/ubuntu.ttf", 30)
                    bordered_text(draw=draw, font=font, thiccness=1, text=text, fill=(255, 255, 255, 255),
                                  outline=(0, 0, 0, 255), xy=(300 + size, 220))

                template.paste(border, (15, 18), border)

                buffer = BytesIO()
                template.save(buffer, 'png')
                buffer.seek(0)
                return buffer

        bf = await self.bot.loop.run_in_executor(None, process_image)

        await message.edit(content='sending file...')
        await ctx.send(file=discord.File(fp=bf, filename='rank.png'))
        total = time.time() - start
        await message.edit(content=f'Total: `{round(total, 3)}s\n{tip}`')

    @_rank.command()
    async def color(self, ctx, *, new_color):
        try:
            new_color = Color(new_color)
        except ValueError:
            return await ctx.send(f'Could not make a color out of `{new_color}`.')

        h = new_color.hex_l
        async with self.bot.db.cursor() as cur:
            query = 'UPDATE leveling SET color = ? WHERE user_id = ?'
            await cur.execute(query, (h, ctx.author.id))
            await self.bot.db.commit()

        image = Image.new(mode='RGB', color=h, size=(128, 128))
        buffer = BytesIO()
        await self.bot.loop.run_in_executor(None, image.save, buffer, 'png')
        buffer.seek(0)
        await ctx.send(f'Changed your rank color to this:', file=discord.File(fp=buffer, filename='color.png'))

    @_rank.command()
    async def image(self, ctx, image_url):
        async with self.bot.db.cursor() as cur:
            query = 'UPDATE leveling SET url = ? WHERE user_id = ?'
            await cur.execute(query, (image_url, ctx.author.id))
            await self.bot.db.commit()

        await ctx.send('Changed your rank image.')


def setup(bot):
    bot.add_cog(Levels(bot))
