import asyncio
import functools
import itertools
import math 
import random

import discord
from discord import colour
from discord import client
from discord.ext import commands
import youtube_dl
import pafy



class music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.song_queue = {}

        self.setup()

    def setup(self, client):
        for guild in self.client.guilds:
            self.song_queue[guild.id] = []

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send('You are not in a voice channel!')
        if not ctx.voice_client:
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()
        else:
            await ctx.send('Already joined voice channel!')
            return


    @commands.command()
    async def disconnect(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        else:
            await ctx.send('I am not in a voice channel!')
            return

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    YDL_OPTIONS = {'format': 'bestaudio/best', 'quiet' : True}

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            ctx.voice_client.stop()
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):
        info = await self.client.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(self.YDL_OPTIONS).extract_info(f'ytsearch{amount}:{song}', download=False, ie_key = 'YoutubeSearch'))
        if len(info['entries']) == 0: return None

        return [entry['webpage_url'] for entry in info['entries']] if get_url else info

    async def play_song(self, ctx, song):
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.client.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5

    @commands.command()
    async def play(self, ctx, *, song=None):
        if song is None:
            return await ctx.send("You must include a song.")
        
        if ctx.voice_client is None:
            return await ctx.send("I am not in a voice channel!")

        if not ('youtube.com/watch?' in song or 'https://youtu.be/' in song):
            await ctx.send('Searching for song...')

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send('Could not find song.')
            
            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f'Currently playing a song, new song has been added to to position {queue_len+1}.')
            else:
                return await ctx.send('Sorry, max queue is 10 songs. Please wait for the current song to end.')
        
        await self.play_song(ctx, song)
        await ctx.send(f'Now playing: {song}')

    @commands.command
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send('Include a song to search for.')

        await ctx.send('Searching for song...')

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Results for '{song}':", description='You can use these urls to play the exact song if this isnot the first result.*\n', colour=discord.Colour.red())

        amount = 0
        for entry in info['entries']:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f'Displaying the first {amount} results')
        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue.")

        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text="Thanks for using me!")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("I am not currently playing any songs for you.")

        poll = discord.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}", description="**80% of the voice channel must vote to skip for it to pass.**", colour=discord.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no
        
        await asyncio.sleep(15) # 15 seconds to vote

        poll_msg = await ctx.channel.fetch_message(poll_id)
        
        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = discord.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=discord.Colour.green())

        if not skip:
            embed = discord.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=discord.Colour.red())

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)

    @commands.command(aliases=['p', 'stop'])
    async def pause(self, ctx):
        ctx.voice_client.pause()
        await ctx.send('Paused')

    @commands.command(aliases=['r', 'continue'])
    async def resume(self, ctx):
        ctx.voice_client.resume()
        await ctx.send('Resume')

async def setup():
    await client.wait_until_ready()
    client.add_cog(music(client))

client.loop.create_task(setup())