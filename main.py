import asyncio
import discord
import os
import requests

from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

# Super secret stuff - get these from me if you're running locally (Nick/Emo)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TWITCH_BEARER_TOKEN = os.getenv("TWITCH_BEARER_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")

# Kinda secret stuff - I still don't want to commit these but they're publicly available
DISCORD_GUILD = os.getenv("DISCORD_GUILD")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

#SPEEDRUN_TAG_ID = '7cefbf30-4c3e-4aa7-99cd-70aabb662f27'
SPEEDRUN_TAG_ID = '6ea6bca4-4712-4ab9-a906-e3336a9d8039' # This is actually the English tag. Uncomment this line for testing

client = discord.Client()
already_live_speedruns = [] # List of live streamers that have already been posted in the channel to avoid dupes
recently_offline = [] # List of streamers who have gone offline and their message needs to be deleted from the channel

async def call_twitch():
    # Waiting period between Twitch API calls - this is first so the bot can connect to Discord on init
    await asyncio.sleep(120)
    url = 'https://api.twitch.tv/helix/streams?game_id=13765'
    # TODO - Automate refreshing the Bearer token - it expires after 60 days
    headers = {'Authorization' : 'Bearer ' + TWITCH_BEARER_TOKEN, 'Client-Id': TWITCH_CLIENT_ID}
    return requests.get(url, headers=headers)

def is_speedrun(stream):
    if stream['tag_ids']:
        return SPEEDRUN_TAG_ID in stream['tag_ids']
    return False

async def get_speedruns(twitch_response):
    streams = twitch_response.json()['data']
    if not streams:
        return []
    return list(filter(is_speedrun, streams))

async def send_discord_messages(speedrun_channels):
    discord_channel = client.get_channel(DISCORD_CHANNEL_ID)
    for channel in speedrun_channels:
        user_name = channel['user_name']
        title = channel['title']
        if user_name not in already_live_speedruns:
            already_live_speedruns.append(user_name)
            output = user_name + " is live with: \n\n**" + title + "**\n\nWatch LIVE at: https://www.twitch.tv/" + user_name
            await discord_channel.send(output)

    # Check if anyone in the list has gone offline and remove them so they send a new post when live again
    live_channel_names = list((channel['user_name'] for channel in speedrun_channels))
    for channel in already_live_speedruns:
        if channel not in live_channel_names:
            already_live_speedruns.remove(channel)
            recently_offline.append(channel)

def is_offline(msg):
    for channel in recently_offline:
        if "Watch LIVE at: https://www.twitch.tv/" + channel in msg.content:
            return True
    return False

async def delete_discord_messages():
    discord_channel = client.get_channel(DISCORD_CHANNEL_ID)
    await discord_channel.purge(limit=100, check=is_offline)
    recently_offline = []

async def main_task():
    while True:
        twitch_response = await call_twitch()
        speedrun_channels = await get_speedruns(twitch_response)
        await send_discord_messages(speedrun_channels)
        await delete_discord_messages()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == DISCORD_GUILD:
            break
    await client.change_presence(activity=discord.Game("Donkey Kong 64"))
    print("Connected")

loop = asyncio.get_event_loop()
loop.create_task(client.start(DISCORD_TOKEN))
loop.create_task(main_task())
loop.run_forever()
