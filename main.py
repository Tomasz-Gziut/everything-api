import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from fastapi import FastAPI
import asyncio

# ================== DISCORD ==================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="create", description="Create a new text channel")
@app_commands.describe(channel_name="Name of the channel to create")
async def create(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message("Server only command.")
        return

    new_channel = await guild.create_text_channel(name=channel_name)

    await interaction.response.send_message(
        f"Channel {new_channel.mention} created!"
    )

# ================== FASTAPI ==================
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot działa!"}

# 🔥 TO JEST KLUCZ
@app.on_event("startup")
async def start_bot():
    asyncio.create_task(bot.start(TOKEN))