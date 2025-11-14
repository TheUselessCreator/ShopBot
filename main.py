import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STATUS = os.getenv("STATUS", "Redeeming Keys")

GUILD_ID = 1432550511495610472  # your guild

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


async def load_utils():
    for filename in os.listdir("./utils"):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            try:
                __import__(f"utils.{module_name}")
                print(f"✅ Loaded util: {module_name}")
            except Exception as e:
                print(f"❌ Util load failed {module_name}: {e}")


async def load_commands():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            try:
                await bot.load_extension(f"commands.{module_name}")
                print(f"✅ Loaded command: {module_name}")
            except Exception as e:
                print(f"❌ Command load failed {module_name}: {e}")


# FIX: Sync must be done in setup_hook, after loading extensions
@bot.event
async def setup_hook():
    print("🔄 Loading utilities...")
    await load_utils()

    print("🔄 Loading commands...")
    await load_commands()

    # Sync to GUILD instantly (instant slash command update)
    guild = discord.Object(id=GUILD_ID)
    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"🏠 Synced {len(synced)} commands to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Guild sync failed: {e}")

    # Global sync (takes up to 1 hour)
    try:
        global_synced = await bot.tree.sync()
        print(f"🌍 Synced {len(global_synced)} global commands")
    except Exception as e:
        print(f"❌ Global sync failed: {e}")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(STATUS))
    print(f"✅ Bot ready: {bot.user} (ID: {bot.user.id})")


async def main():
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
