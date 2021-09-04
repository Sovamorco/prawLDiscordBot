from traceback import print_exception

from credentials import discord_alpha_token, discord_prawl_token, dev
from discord.ext.commands import MissingRequiredArgument, BadArgument

from cogs.bhapi import *


@prawl.listen()
async def on_ready():
    prawl.add_cog(BrawlhallaCog())
    print(f'Logged in as {prawl.user.name}')


@prawl.listen()
async def on_command_error(ctx, error):
    if isinstance(error, MissingRequiredArgument):
        return await ctx.send(f'Usage: `{ctx.prefix}{ctx.command.usage or ctx.command.name}`')
    elif isinstance(error, BadArgument):
        return await ctx.send(f'Bad argument type\nUsage: `{ctx.prefix}{ctx.command.usage or ctx.command.name}`')
    elif isinstance(error, (InvalidURLError, NoBHProfile, NoRankedData)):
        return await ctx.send(error.original)
    elif isinstance(error, CommandInvokeError) and str(error.original):
        print_exception(type(error), error, error.__traceback__)
        return await ctx.send(f'Error:\n```{error.original}```')


prawl.run(discord_alpha_token if dev else discord_prawl_token)
