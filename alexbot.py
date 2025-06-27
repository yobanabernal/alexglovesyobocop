# --- Global Variables ---
already_checked_matches = set()
win_counter = 0
last_match_time = datetime.datetime.utcnow()
last_goodnight_sent = None
last_celebrated_match_id = None
last_love_note_sent = None  # Added for fix #3

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
    if response.status_code != 200:
        print(f"⚠️ Riot API Error {response.status_code}: {response.text}")
    return response.json() if response.status_code == 200 else []

def get_match_details(match_id):
    url = f"https://{PLATFORM_ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"⚠️ Riot API Error {response.status_code}: {response.text}")
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
    global last_love_note_sent
    now = datetime.datetime.utcnow()
    if now.hour == 6 and now.minute == 11:  # 6:11 UTC ≈ 11:11 EST
        if not last_love_note_sent or (now - last_love_note_sent).total_seconds() > 3600:
            await send_message(random.choice(love_notes))
            await asyncio.sleep(2)
            await send_message("🌙 Good night Alex! Sweet dreams from YB! 💖✨")
            last_love_note_sent = now

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
