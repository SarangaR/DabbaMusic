import asyncio
import functools
import itertools
import math 
import random

import discord
from discord.ext import commands
import youtube_dl


class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        }

    ytdl = youtube_dl.YoutubeDL(YDL_OPTIONS)

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
    YDL_OPTIONS = {'format': 'bestaudio/best'}

    ytdl = youtube_dl.YoutubeDL(YDL_OPTIONS)

    @commands.command()
    async def play(self, ctx, url):
        vc = ctx.voice_client
        await ctx.send('Playing...')
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download = False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
            vc.play(source)

    @commands.command()
    async def search(cls, ctx, search: str, *, loop):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            await ctx.send('Couldn\'t find anything that matches `{}`'.format(search))
        
        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break
        
        if process_info is None:
            await ctx.send('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            await ctx.send('Couldn\'t fetch `{}`'.format(webpage_url))
        
        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    await ctx.send('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        source = cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)
        vc = ctx.voice_client
        vc.play(source)

    @commands.command(aliases=['p', 'stop'])
    async def pause(self, ctx):
        ctx.voice_client.pause()
        await ctx.send('Paused')

    @commands.command(aliases=['r', 'continue'])
    async def resume(self, ctx):
        ctx.voice_client.resume()
        await ctx.send('Resume')

def setup(client):
    client.add_cog(music(client))