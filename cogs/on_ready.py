from discord.ext import commands, tasks
import discord
import aiosqlite3
import time


class OnReady(commands.Cog):

    def __init__(self, bot):
        self.leveling = {}
        self.bot = bot
        self.bot.loop.create_task(self.on_ready())

    @tasks.loop(seconds=4.20)
    async def loop(self):

        try:
            async with self.bot.db.cursor() as cur:
                query = 'SELECT user_id FROM muted WHERE muted_until < ?'
                await cur.execute(query, (time.time(),))
                muted_ids = await cur.fetchall()
                query = 'SELECT user_id FROM tempbanned WHERE banned_until < ?'
                await cur.execute(query, (time.time(),))
                banned_ids = await cur.fetchall()
                query = 'DELETE FROM muted WHERE muted_until < ?'
                await cur.execute(query, (time.time(),))
                query = 'DELETE FROM tempbanned WHERE banned_until < ?'
                await cur.execute(query, (time.time(),))

            if muted_ids:
                guild = self.bot.get_guild(self.bot.guild_id)
                role = guild.get_role(self.bot.muted_role_id)
                for muted_id in muted_ids:
                    member = guild.get_member(muted_id[0])
                    try:
                        await member.remove_roles(role)
                    except discord.Forbidden:
                        pass
            if banned_ids:
                guild = self.bot.get_guild(self.bot.guild_id)
                for banned_id in banned_ids:
                    user = discord.Object(id=banned_id[0])
                    await guild.unban(user)

        except Exception as e:
            print(e)

    async def on_ready(self):
        await self.bot.wait_until_ready()
        db = await aiosqlite3.connect('./main.db')
        queries = [
            '''CREATE TABLE IF NOT EXISTS warnings (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "mod_id" INTEGER,
                "reason" TEXT,
                "time" INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS muted (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "muted_at" INTEGER,
                "muted_until" INTEGER,
                "reason" TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS tempbanned (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "banned_at" INTEGER,
                "banned_until" INTEGER,
                "reason" TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS suggestion_cooldowns (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "reset_time" INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS leveling (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "xp" INTEGER,
                "color" TEXT,
                "url" TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS tags (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT,
                "response" TEXT,
                "uses" TEXT,
                "creator_id" INTEGER,
                "created_at" INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS npcs (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "alias" TEXT,
                "name" TEXT,
                "avatar_url" TEXT,
                "granted" TEXT,
                "creator_id" INTEGER
            )''',
            '''CREATE TABLE IF NOT EXISTS counts (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "user_id" INTEGER,
                "nickname" TEXT,
                "count" INTEGER,
                "word" TEXT
            )'''
        ]
        async with db.cursor() as cur:
            for query in queries:
                await cur.execute(query)
            await db.commit()

            self.bot.db = db
            self.loop.start()

            query = 'SELECT user_id, xp FROM leveling'
            await cur.execute(query)
            rows = await cur.fetchall()

            self.bot.leveling = self.leveling

            for row in rows:
                self.bot.leveling[row[0]] = row[1]

            await cur.execute('SELECT name FROM tags')
            self.bot.tag_names = [x[0] for x in await cur.fetchall()]

            await cur.execute('SELECT alias FROM npcs')
            self.bot.npc_aliases = [x[0] for x in await cur.fetchall()]

        activity = discord.Activity(type=discord.ActivityType.watching, name="PMP's Grave")
        await self.bot.change_presence(activity=activity)


def setup(bot):
    bot.add_cog(OnReady(bot))
