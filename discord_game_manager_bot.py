"""
@File    :   discord_game_manager_bot.py
@Time    :   2024/05/18 20:32:52
@Author  :   Thomas Obarowski
@Version :   1.0
@Contact :   tjobarow@gmail.com
@Link    :   https://github.com/tjobarow
@License :   The MIT License 2024
@Description    :   Runs the Game Server Manager discord bot
"""

# Import built in modules
import os
import sys
import json
import logging
import logging.handlers
import random
from datetime import datetime

# Import third party modules
import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord_game_manager.modules.ServerMonitor import ServerMonitor
from discord_game_manager.modules.ServerMonitor import ServerMonitorError

load_dotenv("./config/.discord-env")
load_dotenv("./config/.server-env")


description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True
intents.emojis_and_stickers = True

bot = commands.Bot(
    command_prefix="!", description=description, intents=intents, help_command=None
)


#### START BOT
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.command("lol")
async def lol(ctx):
    lol_msg: str = ("lolo" * 50) + "l"
    await ctx.send(lol_msg, tts=True)


@bot.command("oranges")
async def oranges(ctx):
    oranges_str: str = """
    WHY are all of your Naval Oranges (non organic) from South Africa?! The organic ones are USA...hmmmm... so sick of my food coming from other countries...BUY USA!
    """
    await ctx.message.add_reaction("😡")
    await ctx.send(oranges_str, tts=True)


###################################
# GAME MANAGER CODE
###################################

#### DEFINE RBAC ROLES


def has_a_gamemanager_role():
    def predicate(ctx):
        allowed_roles = [
            "Bot Manager - Status Permission",
            "Bot Manager - Restart Permission",
        ]
        if not any(role.name in allowed_roles for role in ctx.author.roles):
            raise commands.MissingAnyRole(allowed_roles)
        print(
            f"{ctx.author} has role: {list(role.name in allowed_roles for role in ctx.author.roles)}"
        )
        return any(role.name in allowed_roles for role in ctx.author.roles)

    return commands.check(predicate)


def has_gamemanager_restart_role():
    def predicate(ctx):
        allowed_roles = ["Bot Manager - Restart Permission"]
        if not any(role.name in allowed_roles for role in ctx.author.roles):
            raise commands.MissingRole(f", ".join(allowed_roles))
        print(
            f"{ctx.author} has role: {list(role.name in allowed_roles for role in ctx.author.roles)}"
        )
        return any(role.name in allowed_roles for role in ctx.author.roles)

    return commands.check(predicate)


def has_gamemanager_status_role():
    def predicate(ctx):
        allowed_roles = ["Bot Manager - Status Permission"]
        if not any(role.name in allowed_roles for role in ctx.author.roles):
            raise commands.MissingRole(f", ".join(allowed_roles))
        print(
            f"{ctx.author} has role: {list(role.name in allowed_roles for role in ctx.author.roles)}"
        )
        return any(role.name in allowed_roles for role in ctx.author.roles)

    return commands.check(predicate)


@bot.group()
@has_a_gamemanager_role()
async def gamemanager(ctx):
    if ctx.subcommand_passed is None:
        await help(ctx)
    elif ctx.subcommand_passed not in gamemanager.all_commands:
        raise commands.CommandNotFound(ctx.subcommand_passed)


@gamemanager.error
async def gamemanager_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(error)
    if isinstance(error, commands.CommandNotFound):
        await ctx.message.add_reaction("❓")
        await ctx.message.add_reaction("❌")
        await ctx.message.add_reaction("🚫")
        await ctx.send(f"Nice try. This command isn't supported: {error}")


##############################
# GAME MANAGER RESTART PROCESS
@gamemanager.command("restart")
@has_gamemanager_restart_role()
async def restart(ctx, process_name: str = None):
    if process_name is None:
        raise commands.BadArgument(
            f"You must provide the name of the process to restart, such as ```!gamemanager restart valheim-server```"
        )
    await ctx.send(f"Process {process_name} will be restarted.")
    await ctx.send(f"The process {process_name} has been restarted successfully.")


@restart.error
async def restart_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(error)
    if isinstance(error, commands.BadArgument):
        await ctx.send(error)


##############################


##############################
# GAME MANAGER VIEW ALL PROCESSES
@gamemanager.command("status")
@has_gamemanager_status_role()
async def status(ctx):
    await ctx.send(f"status of processes")


@status.error
async def status_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(error)


##############################


##############################
# GAME MANAGER HELP
@gamemanager.command("help")
@has_a_gamemanager_role()
async def help(ctx):
    embed_msg = discord.Embed(color=None, title="Game Manager Help", type="rich")
    embed_msg.set_author(name="Thomas Obarowski")
    embed_msg.add_field(
        name="Introduction",
        value="The gamemanager command will help you interact with the Valheim server running within docker.",
    )
    await ctx.send(
        """The game manager bot is aimed at assisting the gamers with viewing the status of the Valheim Container, and interacting with it's processes, if necessary.
    Usage:
        !gamemanager view - view a list of all Valheim related processes running with the container, including the 'Valheim Server' itself.
        !gamemanager restart <process name> - Provide the bot a process name (from !gamemager view) to restart.
    
    Required Permissions:
        !gamemanager - You must have at least one of the following server roles: Bot Manager - Status Permission, Bot Manager - Restart Permission
        !gamemanager view - You must have the 'Bot Manager - Status Permission' server role.
        !gamemanager restart - You must have the 'Bot Manager - Restart Permission' server role."""
    )


@help.error
async def help_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(error)


###################################
# END GAME MANAGER CODE
###################################


logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="./logs/gamemanager-discord-bot.log",
    encoding="utf-8",
    maxBytes=50 * 1024 * 1024,  # 50 MiB
    backupCount=5,  # Rotate through 5 files
)

consoleHandler = logging.StreamHandler(sys.stdout)

dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(consoleHandler)

bot.run(os.getenv("discord_token"), log_handler=None)
