import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
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

_subprocesses: list[asyncio.subprocess.Process] = []
BASE_DIR = Path(__file__).parent

@app.get("/")
async def home():
    return {"status": "Bot działa!"}

# ====== START BOT + SUBMODULES ======
@app.on_event("startup")
async def startup():
    asyncio.create_task(bot.start(TOKEN))

    def submodule_env(subdir: Path, extra: dict = {}) -> dict:
        """Merge os.environ + submodule's .env file + any extra overrides."""
        env = {**os.environ}
        dot_env = subdir / ".env"
        if dot_env.exists():
            env.update(dotenv_values(dot_env))
        env.update(extra)
        return env

    # Open-Router-cake on port 8001
    open_router_dir = BASE_DIR / "Open-Router-cake"
    if (open_router_dir / "main.py").exists():
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0", "--port", "8001",
            cwd=str(open_router_dir),
            env=submodule_env(open_router_dir),
        )
        _subprocesses.append(proc)
        print(f"[submodule] Open-Router-cake started on port 8001 (pid {proc.pid})")
    else:
        print("[submodule] Open-Router-cake not found, skipping")

    # heartbeat on port 8888, pinging main + open-router-cake
    heartbeat_dir = BASE_DIR / "heartbeat"
    if (heartbeat_dir / "__main__.py").exists():
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "heartbeat",
            cwd=str(heartbeat_dir),
            env=submodule_env(heartbeat_dir, {
                "HEARTBEAT_PORTS": "8000,8001",
                "HEARTBEAT_PORT": "8888",
            }),
        )
        _subprocesses.append(proc)
        print(f"[submodule] heartbeat started on port 8888 (pid {proc.pid})")
    else:
        print("[submodule] heartbeat not found, skipping")

@app.on_event("shutdown")
async def shutdown():
    for proc in _subprocesses:
        proc.terminate()
    if _subprocesses:
        await asyncio.gather(*[proc.wait() for proc in _subprocesses])
        print(f"[submodule] {len(_subprocesses)} submodule(s) stopped")