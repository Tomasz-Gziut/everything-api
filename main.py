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

# ====== CREATE TEXT CHANNEL ======
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

# ====== CREATE CATEGORY ======
@bot.tree.command(name="create_category", description="Create a new category")
@app_commands.describe(category_name="Name of the category to create")
async def create_category(interaction: discord.Interaction, category_name: str):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message("Server only command.")
        return

    new_category = await guild.create_category(name=category_name)

    await interaction.response.send_message(
        f"Category **{new_category.name}** created!"
    )

# ====== CREATE CATEGORY + CHANNEL ======
@bot.tree.command(name="create_category_with_channel", description="Create category with a channel")
@app_commands.describe(
    category_name="Name of the category",
    channel_name="Name of the channel"
)
async def create_category_with_channel(
    interaction: discord.Interaction,
    category_name: str,
    channel_name: str
):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message("Server only command.")
        return

    category = await guild.create_category(name=category_name)
    channel = await guild.create_text_channel(name=channel_name, category=category)

    await interaction.response.send_message(
        f"Created category **{category.name}** with channel {channel.mention}"
    )

# ================== FASTAPI ==================
app = FastAPI()

@app.get("/")
async def home():
    return {"status": "Bot działa!"}

# ====== START BOT ======
@app.on_event("startup")
async def start_bot():
    asyncio.create_task(bot.start(TOKEN))