import discord
import json
from discord.ext import commands
import music
import os

TOKEN = os.getenv('DISCORD_TOKEN')

globalPrefix = '.'

client = commands.Bot(command_prefix = globalPrefix, intents = discord.Intents.all())

@client.command(aliases=['cp', 'prefix'])
async def changeprefix(ctx, prefix):
    global globalPrefix
    globalPrefix = prefix
    await ctx.send(f'New prefix: {prefix}')

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('Music Bot'))
    print(f'Logged in as {client.user}')

async def setup():
    await client.wait_until_ready()
    client.add_cog(music(client))

client.loop.create_task(setup())
client.run(TOKEN)