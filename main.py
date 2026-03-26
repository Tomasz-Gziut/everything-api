import configparser
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

# ================== SUBMODULE DISCOVERY ==================
BASE_DIR = Path(__file__).parent


def _read_submodule_paths() -> list[Path]:
    config = configparser.ConfigParser()
    config.read(BASE_DIR / ".gitmodules")
    paths = []
    for section in config.sections():
        if "path" in config[section]:
            p = BASE_DIR / config[section]["path"]
            if p.is_dir():
                paths.append(p)
    return paths


def _submodule_python(subdir: Path) -> str:
    venv_python = subdir / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def _detect_entry(subdir: Path) -> str | None:
    """Return 'uvicorn:main:app', 'uvicorn:app:app', 'module', or None."""
    if (subdir / "main.py").exists():
        return "uvicorn:main:app"
    if (subdir / "app.py").exists():
        return "uvicorn:app:app"
    if (subdir / "__main__.py").exists():
        return "module"
    return None


# ================== FASTAPI ==================
app = FastAPI()

_subprocesses: list[asyncio.subprocess.Process] = []

@app.get("/")
async def home():
    return {"status": "Bot działa!"}

# ====== START BOT + SUBMODULES ======
@app.on_event("startup")
async def startup():
    asyncio.create_task(bot.start(TOKEN))

    def submodule_env(subdir: Path, extra: dict = {}) -> dict:
        env = {**os.environ}
        dot_env = subdir / ".env"
        if dot_env.exists():
            env.update(dotenv_values(dot_env))
        env.update(extra)
        return env

    submodules = _read_submodule_paths()
    main_port = int(os.getenv("PORT", "8000"))
    next_port = 8001
    api_ports = [main_port]  # track all running API ports for sidecar services

    # First pass: start uvicorn-style APIs and assign them sequential ports
    module_services = []
    for subdir in submodules:
        entry = _detect_entry(subdir)
        if entry is None:
            print(f"[submodule] {subdir.name}: no entry point found, skipping")
            continue

        if entry.startswith("uvicorn:"):
            _, module, attr = entry.split(":")
            port = next_port
            next_port += 1
            proc = await asyncio.create_subprocess_exec(
                _submodule_python(subdir), "-m", "uvicorn", f"{module}:{attr}",
                "--host", "0.0.0.0", "--port", str(port),
                cwd=str(subdir),
                env=submodule_env(subdir),
            )
            _subprocesses.append(proc)
            api_ports.append(port)
            print(f"[submodule] {subdir.name} started on port {port} (pid {proc.pid})")
        else:
            module_services.append(subdir)

    # Second pass: start module-style services (e.g. heartbeat) with all known ports
    for subdir in module_services:
        proc = await asyncio.create_subprocess_exec(
            _submodule_python(subdir), "-m", subdir.name,
            cwd=str(subdir),
            env=submodule_env(subdir, {
                "HEARTBEAT_PORTS": ",".join(str(p) for p in api_ports),
            }),
        )
        _subprocesses.append(proc)
        print(f"[submodule] {subdir.name} started (pid {proc.pid})")

@app.on_event("shutdown")
async def shutdown():
    for proc in _subprocesses:
        proc.terminate()
    if _subprocesses:
        await asyncio.gather(*[proc.wait() for proc in _subprocesses])
        print(f"[submodule] {len(_subprocesses)} submodule(s) stopped")