from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import discord
from dotenv import load_dotenv

if TYPE_CHECKING:
    from discord import Interaction

load_dotenv()

TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()


@tree.command()
async def ping(interaction: Interaction):
    s = time.perf_counter()
    await interaction.response.send_message("Pong! ...")
    e = time.perf_counter()

    await interaction.edit_original_response(content=f"Pong! `{(e - s) * 1000:.2f}ms`")


client.run(TOKEN)
