from traceback import print_exception

from credentials import discord_alpha_token, discord_prawl_token
from discord import Game
from discord.ext.commands import BadArgument

from cogs.bhapi import *


@prawl.listen()
async def on_ready():
    prawl.add_cog(BrawlhallaCog())
    await prawl.change_presence(activity=Game(name='prr help | i\'m open-source at github.com/sovamorco :3'))
    print(f'Logged in as {prawl.user.name}')


@prawl.command(name='help')
async def _help(ctx):
    return await ctx.send(f'Commands: `help`, `rank`, `link`, `unlink`')


@prawl.listen()
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        return await ctx.send(f'Usage: `{ctx.prefix}{ctx.command.usage or ctx.command.name}`')
    elif isinstance(error, BadArgument):
        return await ctx.send(f'Bad argument type\nUsage: `{ctx.prefix}{ctx.command.usage or ctx.command.name}`')
    elif isinstance(error, (InvalidURLError, NoBHProfile, NoRankedData, InvalidNameError, RateLimitError, APIError)):
        return await ctx.send(error.original)
    elif isinstance(error, NoError):
        return
    elif isinstance(error, CommandInvokeError) and str(error.original):
        print_exception(type(error), error, error.__traceback__)
        return await ctx.send(f'Error:\n```{error.original}```')


prawl.run(discord_alpha_token if dev else discord_prawl_token)
