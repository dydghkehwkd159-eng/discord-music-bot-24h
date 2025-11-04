import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import os

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

queues = {}

@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")

# 유튜브에서 오디오 소스 가져오기
def get_source(url):
    ydl_opts = {'format': 'bestaudio', 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info.get('title', '제목 없음')

# 재생 명령어 (자동 입장)
@bot.slash_command(name="재생", description="음악을 재생합니다.")
async def 재생(ctx, url: str):
    if not ctx.author.voice:
        await ctx.respond("🔇 먼저 음성 채널에 들어가 주세요.")
        return

    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await voice_channel.connect()

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    stream_url, title = get_source(url)
    if len(queues[ctx.guild.id]) >= 800:
        await ctx.respond("⚠️ 대기열이 가득 찼습니다. (최대 800개)")
        return

    queues[ctx.guild.id].append((stream_url, title))
    await ctx.respond(f"🎵 **{title}** 추가됨. (대기열 {len(queues[ctx.guild.id])}/800)")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)

async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id in queues and queues[guild_id]:
        stream_url, title = queues[guild_id].pop(0)
        vc = ctx.voice_client
        vc.play(discord.FFmpegPCMAudio(stream_url), after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f"▶️ 재생 중: **{title}**")
    else:
        await ctx.send("⏹️ 대기열이 비었습니다.")

# 셔플 명령어
@bot.slash_command(name="셔플", description="대기열을 무작위로 섞습니다.")
async def 셔플(ctx):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        await ctx.respond("❌ 대기열이 비어 있습니다.")
        return
    random.shuffle(queues[ctx.guild.id])
    await ctx.respond("🔀 대기열이 섞였습니다!")

# 정지 명령어
@bot.slash_command(name="정지", description="모든 재생을 중단합니다.")
async def 정지(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queues[ctx.guild.id] = []
        await ctx.respond("🛑 음악 재생이 중단되었습니다.")

# 자동 재시작 기능
async def keep_alive():
    while True:
        await asyncio.sleep(600)
        print("🔁 봇 상태 유지 중...")

async def restart_on_crash():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"⚠️ 오류 발생, 5초 후 재시작: {e}")
            await asyncio.sleep(5)

async def main():
    await asyncio.gather(restart_on_crash(), keep_alive())

asyncio.run(main())
