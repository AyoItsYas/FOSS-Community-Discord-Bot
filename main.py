from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import discord
from dotenv import load_dotenv

from utils import message_formatting

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
    message_lines = [
        ["Discord Websocket Latency", f'"{client.latency * 1000:.2f}ms"'],
        ["Discord REST Latency", "..."],
    ]
    format_message_lines = lambda: (
        f"```ml\n{message_formatting.align_to_columns(message_lines, column_sep=' : ')}```"
    )

    s = time.perf_counter()
    await interaction.response.send_message(format_message_lines())
    e = time.perf_counter()

    message_lines[1][1] = f'"{(e - s) * 1000:.2f}ms"'

    await interaction.edit_original_response(content=format_message_lines())


client.run(TOKEN)
