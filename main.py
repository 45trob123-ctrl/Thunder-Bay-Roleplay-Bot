import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=";",
    intents=intents,
    help_command=None
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Thunder Bay Roleplay bot is online!")


@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! `{round(bot.latency * 1000)}ms`")


TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing.")

bot.run(TOKEN)