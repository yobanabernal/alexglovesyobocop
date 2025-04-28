import requests
import random
import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import os

# --- Riot API Info ---
RIOT_API_KEY = "RGAPI-c7f0282c-96cd-4fc3-a065-db2ea8f97a5d"
PUUID = "pQP5alDcqtoLkUqghskgYDMxQ3Rwl62JCjI3TyqgDQpzIB_TpIpVyLcm4u_GnWLTEGhZLQgvIL5Nuw"
PLATFORM_ROUTING = "americas"

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

# --- Channel ID ---
CHANNEL_ID = 1364814276287791166

# --- Image Lists ---
victory_images = [
    "https://i.imgur.com/E3K6diu.png", "https://i.imgur.com/0nlWVAz.png",
    "https://i.imgur.com/8IK05Gj.gif", "https://i.imgur.com/st6CKzA.gif",
    "https://i.imgur.com/nNuvTIy.gif", "https://i.imgur.com/HNBLKT2.gif",
    "https://i.imgur.com/TubCg5S.gif", "https://i.imgur.com/afmRSoq.gif",
    "https://i.imgur.com/rnWqVMv.gif"
]

loss_images = [
    "https://i.imgur.com/TWkICaS.png", "https://i.imgur.com/KA7Vb0f.png",
    "https://i.imgur.com/VZeKY49.gif", "https://i.imgur.com/EwSka7o.gif",
    "https://i.imgur.com/6d0UUg7.gif", "https://i.imgur.com/zJYKUlL.gif",
    "https://i.imgur.com/FBn7die.gif", "https://i.imgur.com/P4kemwD.gif"
]

pentakill_images = [
    "https://i.imgur.com/MNTVx0q.gif", "https://i.imgur.com/qZieswl.gif",
    "https://i.imgur.com/lPwu7Cz.gif", "https://i.imgur.com/7NcBkyF.gif",
    "https://i.imgur.com/fTQKS1l.gif"
]

mvp_images = [
    "https://i.imgur.com/QG8Gutu.png", "https://i.imgur.com/JbNIU35.jpeg",
    "https://i.imgur.com/r0qup5U.jpeg", "https://i.imgur.com/pLOvgF3.jpeg",
    "https://i.imgur.com/rCH1CQ6.jpeg", "https://i.imgur.com/5kv113R.jpeg",
    "https://i.imgur.com/6gWg3wg.jpeg"
]

first_blood_images = [
    "https://i.imgur.com/D1GXeOI.png", "https://i.imgur.com/f5GD2Eg.gif",
    "https://i.imgur.com/A28iUEG.gif", "https://i.imgur.com/oYPqFxB.gif",
    "https://i.imgur.com/f8BWcfb.gif", "https://i.imgur.com/V9B6Oi4.gif"
]

league_victory_messages = [
    "Nexus Destroyed! ⚔️", "Victory Royale! 🎮", "Enemy team FFed at 15! 🏆", "Another LP secured! 🧡"
]

love_notes = [
    "🧡 YB loves you more than all the stars, Alex!",
    "💖 You're YB's favorite champion and favorite person!",
    "🎀 No matter the match, you're always winning my heart.",
    "🌟 Wishing you the sweetest dreams and biggest victories, Alex!",
    "🏆 YB is always your #1 fan, no matter what!"
]

goodnight_messages = [
    "🌙 Time to log off, builder Alex. Sweet dreams of diamonds and creepers! 🧱✨",
    "🌙 Good night King Alex, may your dreams be filled with whoppers! 🍔👑",
    "🌙 Good night Summoner! Zero feeders, only sweet dreams! 🎮✨",
    "🌙 Dream big like a Kardashian, Alex! 💎🛌",
    "🌙 Lettuce hope you sleep well, burger king! 🥬🍔",
    "🌙 Good night! Hope your ELO dreams are as high as Challenger! 🏆"
]

# --- Global Variables ---
already_checked_matches = set()
win_counter = 0
last_match_time = datetime.datetime.utcnow()
last_goodnight_sent = None
last_celebrated_match_id = None

# --- Helper Functions ---
async def send_embed(image_url, title, color=0x00ff00):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return
    embed = discord.Embed(title=title, color=color)
    embed.set_image(url=image_url)
    embed.set_footer(text="Proudly monitored by YB 🎀")
    await channel.send(embed=embed)

async def send_message(text):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(text)

def save_last_match_id(match_id):
    with open("last_match.txt", "w") as f:
        f.write(match_id)

def load_last_match_id():
    if os.path.exists("last_match.txt"):
        with open("last_match.txt", "r") as f:
            return f.read().strip()
    return None

# --- Riot API ---
def get_recent_match_ids(puuid, count=1):
    url = f"https://{PLATFORM_ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else []

def get_match_details(match_id):
    url = f"https://{PLATFORM_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

# --- Core Logic ---
@tasks.loop(minutes=4)
async def game_check():
    global win_counter, last_match_time, last_goodnight_sent, last_celebrated_match_id

    await asyncio.sleep(10)
    match_ids = get_recent_match_ids(PUUID, count=1)
    if not match_ids:
        return
    latest_match_id = match_ids[0]

    if latest_match_id == last_celebrated_match_id:
        return

    match_data = get_match_details(latest_match_id)
    if not match_data:
        return

    last_match_time = datetime.datetime.utcnow()
    last_goodnight_sent = None
    last_celebrated_match_id = latest_match_id
    save_last_match_id(latest_match_id)

    participant = next((p for p in match_data['info']['participants'] if p['puuid'] == PUUID), None)
    if not participant:
        return

    if participant['win']:
        win_counter += 1
        victory_caption = random.choice(league_victory_messages)
        image_url = random.choice(victory_images)
        await send_embed(image_url, f"🏆 Victory #{win_counter}! {victory_caption}", color=0xFFD700)
    else:
        image_url = random.choice(loss_images)
        await send_embed(image_url, "😭 Defeat...", color=0xFF5555)

    if participant.get('firstBloodKill', False):
        image_url = random.choice(first_blood_images)
        await send_embed(image_url, "🩸 First Blood!", color=0xDC143C)

    if participant.get('pentaKills', 0) > 0:
        image_url = random.choice(pentakill_images)
        await send_embed(image_url, "💥 Pentakill!", color=0xFFA500)

    highest_damage = max(p['totalDamageDealtToChampions'] for p in match_data['info']['participants'])
    if participant['totalDamageDealtToChampions'] == highest_damage:
        image_url = random.choice(mvp_images)
        await send_embed(image_url, "🌟 MVP!", color=0x800080)

    if participant.get('pentaKills', 0) > 0 and participant['totalDamageDealtToChampions'] == highest_damage:
        await send_message("🌟🏆 LEGENDARY GAME! MVP and Pentakill achieved! YB is screaming right now! 🎀🎮💖")

@tasks.loop(minutes=1)
async def inactivity_check():
    global last_goodnight_sent
    now = datetime.datetime.utcnow()
    if (now - last_match_time).total_seconds() >= 3600 and (not last_goodnight_sent or (now - last_goodnight_sent).total_seconds() >= 3600):
        message = random.choice(goodnight_messages)
        await send_message(message)
        last_goodnight_sent = now

@tasks.loop(minutes=1)
async def daily_love_note():
    now = datetime.datetime.now()
    if now.hour == 23 and now.minute == 11:
        await send_message(random.choice(love_notes))
        await asyncio.sleep(300)
        await send_message("🌙 Good night Alex! Sweet dreams from YB! 💖✨")

# --- Events ---
@client.event
async def on_ready():
    global last_celebrated_match_id
    print(f"✅ Logged in as {client.user}")
    last_celebrated_match_id = load_last_match_id()
    await send_message("🧡 Alexbot is online and ready to support Alex and YB! 🎀")
    game_check.start()
    inactivity_check.start()
    daily_love_note.start()

# --- Run Bot ---
client.run(os.getenv("DISCORD_TOKEN"))
