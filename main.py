from __future__ import annotations

import asyncio
import io
import os
import pprint
import textwrap
import logging
import traceback
from contextlib import redirect_stdout
from dotenv import load_dotenv
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from utils import Timer, TextFormatter

if TYPE_CHECKING:
    from typing import Union

    from discord import Interaction

logger = logging.getLogger(__name__)

load_dotenv()


TOKEN = os.getenv("DISCORD_TOKEN")
ERROR_LOG_CHANNEL: Union[discord.TextChannel, None] = None


intents = discord.Intents.default()

intents.members = True
intents.message_content = True

discord_client = commands.Bot("/", intents=intents)


@discord_client.event
async def on_ready():
    await discord_client.tree.sync()


utility_commands = app_commands.Group(name="utility", description="Utility Commands")


@utility_commands.command()
async def ping(interaction: Interaction):
    message_lines = [
        ["Discord Websocket", f'"{discord_client.latency * 1000:.2f}ms"'],
        ["Discord REST", "..."],
    ]
    format_message_lines = lambda: (
        f"```ml\n{TextFormatter.align_to_columns(message_lines, column_sep=' : ')}```"
    )

    with Timer() as timer:
        await interaction.response.send_message(
            embed=discord.Embed(description=format_message_lines())
        )

    message_lines[1][1] = f'"{(timer.time) * 1000:.2f}ms"'

    await interaction.edit_original_response(
        embed=discord.Embed(description=format_message_lines())
    )


@commands.is_owner()
@utility_commands.command()
async def execute(interaction: Interaction, *, body: str):
    async with interaction.channel.typing():
        body = await interaction.channel.fetch_message(int(body))
        if body is None:
            await interaction.response.send_message(
                embed=discord.Embed(description="Message not found.")
            )
            return

        body = body.content
        body = body_raw = "\n".join(body.split("\n")[1:-1])

        await interaction.response.send_message(
            embed=discord.Embed(description=f"```py\n{body}```")
        )

        env = {
            "author": interaction.user,
            "channel": interaction.channel,
            "client": discord_client,
            "discord": discord,
            "guild": interaction.guild,
            "response": interaction.response,
            "print": lambda *x, **y: pprint.pprint(*x, indent=4, **y),
            "raw_print": print,
        }

        stdout = io.StringIO()
        to_compile = f'async def executor_body():\n{textwrap.indent(body, "    ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    description=f"```py\n{body_raw}``````py\n{e.__class__.__name__}: {e}\n```"
                )
            )
            return

        executor_body = env["executor_body"]

        try:
            with redirect_stdout(stdout):
                with Timer() as timer:
                    ret = await executor_body()
                exec_time = timer.time
        except Exception as _:  # noqa
            value = stdout.getvalue()
            text = f"```py\n{body_raw}``````py\n{value}{traceback.format_exc()}\n```"
        else:
            value = stdout.getvalue()
            text = f"```py\n{body_raw}``````py\n{value}\n# Returned {ret}, executed in {exec_time * 1000} ms```"

        await interaction.edit_original_response(embed=discord.Embed(description=text))
        return value


@commands.is_owner()
@utility_commands.command()
async def shell(interaction: Interaction, *, body: str):
    import subprocess

    async def run_process(command):
        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            result = await discord_client.loop.run_in_executor(
                None, process.communicate
            )

        return [output.decode() for output in result]

    async with interaction.channel.typing():
        body = await interaction.channel.fetch_message(int(body))
        if body is None:
            await interaction.response.send_message(
                embed=discord.Embed(description="Message not found.")
            )
            return

        body = body.content
        body = "\n".join(body.split("\n")[1:-1])

        await interaction.response.send_message(
            embed=discord.Embed(description=f"```sh\n{body}```")
        )

        stdout, stderr = await run_process(body)

        if stderr:
            text = f"stdout:\n{stdout}\nstderr:\n{stderr}"
        else:
            text = stdout

        await interaction.edit_original_response(
            embed=discord.Embed(description=f"```sh\n{body}``````sh\n{text}```")
        )


discord_client.tree.add_command(utility_commands)


@discord_client.tree.error
async def on_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
):
    match error:
        case app_commands.errors.CommandOnCooldown():
            embed = discord.Embed(
                description=f"You are on cooldown! Try again in {error.retry_after:.2f}s"
            )

            return await interaction.response.send_message(embed=embed)
        case app_commands.errors.MissingPermissions():
            embed = discord.Embed(
                description="You do not have the required permissions to run this command."
            )

            return await interaction.response.send_message(embed=embed)
        case _:
            embed = discord.Embed(description="An unhandled exception occured!")

            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed)
            else:
                await interaction.response.send_message(embed=embed)

            error_tb = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            logger.exception(f"Ignoring exception in event '{error}'\n{error_tb}")

            global ERROR_LOG_CHANNEL

            if not ERROR_LOG_CHANNEL:
                ERROR_LOG_CHANNEL = await discord_client.fetch_channel(
                    os.getenv("ERROR_LOG_CHANNEL_ID")
                )

            log = f"Ignoring exception in event '{error}'\n\n{error_tb}"

            chunks = log.split("\n")
            chunks = [chunks[i : i + 20] for i in range(0, len(chunks), 20)]

            for chunk in chunks:
                await ERROR_LOG_CHANNEL.send(TextFormatter.codeblock("\n".join(chunk)))


discord_client.run(TOKEN)
