import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

queue = []
now_playing = None
voice_client = None

@bot.event
async def on_ready():
    print(f'봇이 로그인되었습니다: {bot.user}')

async def play_next(ctx):
    global now_playing, voice_client
    if queue:
        url = queue.pop(0)
        await play_music(ctx, url)
    else:
        now_playing = None

async def play_music(ctx, url):
    global now_playing, voice_client
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        title = info.get('title', '알 수 없는 제목')

    if not ctx.voice_client:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
        else:
            await ctx.send('🎤 먼저 음성 채널에 들어가 주세요!')
            return

    now_playing = title
    source = await discord.FFmpegOpusAudio.from_probe(url2, method='fallback')
    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f'🎶 재생 중: **{title}**')

@bot.command(name='재생')
async def play(ctx, *, url):
    global now_playing
    if len(queue) >= 800:
        await ctx.send('🚫 대기열이 가득 찼어요 (최대 800개).')
        return

    if ctx.voice_client and ctx.voice_client.is_playing():
        queue.append(url)
        await ctx.send(f'🎵 대기열에 추가됨: {url} (현재 {len(queue)}개)')
    else:
        await play_music(ctx, url)

@bot.command(name='대기열')
async def show_queue(ctx):
    if not queue:
        await ctx.send('📭 대기열이 비어있어요.')
    else:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queue[:20])])
        await ctx.send(f'🎧 **현재 대기열:**\n{msg}')

@bot.command(name='스킵')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('⏭️ 다음 곡으로 넘어갑니다.')
    else:
        await ctx.send('⏹️ 재생 중인 음악이 없습니다.')

@bot.command(name='정지')
async def stop(ctx):
    global queue
    if ctx.voice_client:
        queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send('🛑 음악이 정지되고 봇이 퇴장했습니다.')

@bot.command(name='일시정지')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send('⏸️ 음악을 일시정지했습니다.')
    else:
        await ctx.send('❌ 일시정지할 음악이 없습니다.')

@bot.command(name='다시재생')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send('▶️ 음악을 다시 재생합니다.')
    else:
        await ctx.send('❌ 다시 재생할 음악이 없습니다.')

@bot.command(name='셔플')
async def shuffle_queue(ctx):
    if len(queue) > 1:
        random.shuffle(queue)
        await ctx.send('🔀 대기열을 셔플했습니다!')
    else:
        await ctx.send('❌ 셔플할 노래가 없습니다.')

bot.run(os.getenv("DISCORD_TOKEN"))
