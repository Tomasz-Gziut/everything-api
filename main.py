import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Załaduj zmienne z .env
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

    new_channel = await guild.create_text_channel(name=channel_name)

    await interaction.response.send_message(
        f"Channel {new_channel.mention} created successfully!"
    )

bot.run(TOKEN)