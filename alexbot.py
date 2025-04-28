import requests
import random
import discord
from discord.ext import commands, tasks
import datetime

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

# --- Store last game date for tagline ---
last_game_played = {}
win_counter = 0  # Tracks total victories

# --- Image URLs ---
liar_images = [
    "https://i.imgur.com/zv2pyCo.png"
]

victory_images = [
    "https://i.imgur.com/E3K6diu.png",
    "https://i.imgur.com/0nlWVAz.png"
]

loss_images = [
    "https://i.imgur.com/TWkICaS.png",
    "https://i.imgur.com/KA7Vb0f.png"
]

mvp_images = [
    "https://i.imgur.com/QG8Gutu.png"
]

first_blood_images = [
    "https://i.imgur.com/D1GXeOI.png"
]

# --- Taglines ---
taglines = [
    "Let's go, Summoner! AlexBot is watching your every move! 👀",
    "The Rift's waiting for you. Don't let AlexBot down! 💥",
    "First blood or first fall? Let’s see what you got! 🩸",
    "Victory is just around the corner, carry the team! 🏆",
    "Shut down the Nexus, your ally AlexBot believes in you! ⚔️",
    "The enemy’s Nexus won’t destroy itself, carry on! 💪",
    "One more win, and we climb the ranks! AlexBot is cheering! 🎮",
    "First blood? Or first fail? AlexBot’s ready to track it! 💥",
    "AlexBot’s got your back. Time to snowball this game! ⛄",
    "💖 Alexbot is online! Ready to cheer for my favorite gamer~",
    "👀 Watching closely... Let’s see if Alex pops off or feeds again 😘",
    "🎮 Monitoring Summoner 'Replica0702' — battle incoming!",
    "📣 Go Alex go!! Your #1 fan is tracking your matches 💕",
    "✨ I’m watching. Don’t die too much, okay?",
    "🧡 Just here to support my favorite person’s gaming journey."
]

# --- Daily Love Notes ---
love_notes = [
    "🧡 YB loves you more than all the stars, Alex!",
    "💖 You're YB's favorite champion and favorite person!",
    "🎀 No matter the match, you're always winning my heart.",
    "🌟 Wishing you the sweetest dreams and biggest victories, Alex!",
    "🏆 YB is always your #1 fan, no matter what!"
]

# --- Helper Functions ---

def get_recent_match_ids(puuid, count=1):
    url = f"https://{PLATFORM_ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match IDs: {response.status_code}")
        return []

def get_match_details(match_id):
    url = f"https://{PLATFORM_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching match details: {response.status_code}")
        return None

def is_first_game_today(user_id):
    today = datetime.date.today()
    if user_id not in last_game_played or last_game_played[user_id] != today:
        last_game_played[user_id] = today
        return True
    return False

async def send_random_embed_from(image_list, title=""):
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return
    if not image_list:
        print("❌ No images available.")
        return

    image_url = random.choice(image_list)
    embed = discord.Embed(title=title, color=0x00ff00)
    embed.set_image(url=image_url)
    await channel.send(embed=embed)
    print(f"✅ Sent embed: {title}")

async def send_random_tagline():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(random.choice(taglines))

async def send_love_note():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        love_message = random.choice(love_notes)
        await channel.send(love_message)
        print("✅ Sent daily love note.")

# --- Main Match Check ---

already_checked_matches = set()

async def check_latest_match():
    global win_counter

    match_ids = get_recent_match_ids(PUUID, count=1)
    if not match_ids:
        return
    latest_match_id = match_ids[0]

    if latest_match_id in already_checked_matches:
        return  # No new match
    already_checked_matches.add(latest_match_id)

    match_data = get_match_details(latest_match_id)
    if not match_data:
        return

    participant = None
    for p in match_data['info']['participants']:
        if p['puuid'] == PUUID:
            participant = p
            break

    if participant is None:
        print("Participant not found in match.")
        return

    if is_first_game_today(participant['summonerId']):
        await send_random_tagline()

    # Win / Loss
    if participant['win']:
        win_counter += 1
        await send_random_embed_from(victory_images, title=f"🏆 Victory #{win_counter}!")
    else:
        await send_random_embed_from(loss_images, title="😭 Defeat...")

    # Extra Achievements
    mvp = False
    penta = False

    if participant.get('firstBloodKill', False):
        await send_random_embed_from(first_blood_images, title="🩸 First Blood!")

    if participant.get('pentaKills', 0) > 0:
        penta = True
        await send_random_embed_from(liar_images, title="💥 Pentakill!")

    highest_damage = max(p['totalDamageDealtToChampions'] for p in match_data['info']['participants'])
    if participant['totalDamageDealtToChampions'] == highest_damage:
        mvp = True
        await send_random_embed_from(mvp_images, title="🌟 MVP!")

    # Highlight Special Big Moment
    if mvp and penta:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            special_message = "**🌟🏆 LEGENDARY GAME! 🌟🏆**\nAlex got both MVP and Pentakill! YB is soooo proud!!! 🎀🎮💖"
            await channel.send(special_message)
            print("🌟 Sent special highlight message!")

# --- Tasks ---

@tasks.loop(minutes=4)
async def game_check():
    await check_latest_match()

@tasks.loop(minutes=1)
async def daily_love_note():
    now = datetime.datetime.now()
    if now.hour == 23 and now.minute == 11:
        await send_love_note()
        await asyncio.sleep(300)  # Wait 5 minutes (300 seconds)
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("🌙 Good night Alex! Sweet dreams from YB! 💖✨")
            print("✅ Sent Good Night message.")


# --- Events ---

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🧡 Alexbot is online and ready to support Alex and YB! 🎀")
    game_check.start()
    daily_love_note.start()

# --- Run the Bot ---
import os
client.run(os.getenv("DISCORD_TOKEN"))

