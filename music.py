import discord
from discord.ext import commands
import youtube_dl

class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send('You are not in a voice channel!')
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect()

    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, url):
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
             'options': '-vn'
             }
        YDL_OPTIONS = {'format': 'bestaudio'}
        vc = ctx.voice_client
        await ctx.send('Playing...')
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download = False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
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