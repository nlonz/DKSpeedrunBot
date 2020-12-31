import discord
from discord.ext import commands
from discord.utils import get
import asyncio
from pprint import pprint
import requests

# Super secret stuff - get these from me if you're running locally (Nick/Emo)
DISCORD_TOKEN = ''
BEARER_TOKEN = ''
CLIENT_ID = ''

# Kinda secret stuff - I still don't want to commit these but they're publicly available
GUILD = ''
CHANNEL_ID = None

SPEEDRUN_TAG_ID = '7cefbf30-4c3e-4aa7-99cd-70aabb662f27'
#SPEEDRUN_TAG_ID = '6ea6bca4-4712-4ab9-a906-e3336a9d8039' # This is actually the English tag. Uncomment this line for testing

client = discord.Client()
already_live_speedruns = [] # List of live streamers that have already been posted in the channel to avoid dupes

async def call_twitch():
    # Waiting period between Twitch API calls - this is first so the bot can connect to Discord on init
    await asyncio.sleep(60)
    url = 'https://api.twitch.tv/helix/streams?game_id=13765'
    # TODO - Automate refreshing the Bearer token - it expires after 60 days
    headers = {'Authorization' : 'Bearer ' + BEARER_TOKEN, 'Client-Id': CLIENT_ID}
    return requests.get(url, headers=headers)

async def get_speedruns(twitch_response):
    streams = twitch_response.json()['data']
    if not streams:
        return []
    return filter(lambda stream: SPEEDRUN_TAG_ID in stream['tag_ids'], streams)

async def send_discord_messages(speedrun_channels):
    discord_channel = client.get_channel(CHANNEL_ID)
    for channel in speedrun_channels:
        if channel not in already_live_speedruns:
            already_live_speedruns.append(channel)
            output = "" + channel['user_name'] + " is live with: \n\n**" + channel['title'] + "**\n\nWatch LIVE at: https://www.twitch.tv/" + channel['user_name']
            await discord_channel.send(output)

    # Check if anyone in the list has gone offline and remove them so they send a new post when live again
    for channel in already_live_speedruns:
        if channel not in speedrun_channels:
            already_live_speedruns.remove(channel)

async def main_task():
    while True:
        twitch_response = await call_twitch()
        speedrun_channels = await get_speedruns(twitch_response)
        await send_discord_messages(speedrun_channels)

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    print("Connected")

loop = asyncio.get_event_loop()
loop.create_task(client.start(DISCORD_TOKEN))
loop.create_task(main_task())
loop.run_forever()
