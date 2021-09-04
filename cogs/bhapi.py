from discord.ext.commands import Cog, command, CommandInvokeError

from general import *


class InvalidURLError(CommandInvokeError):
    def __init__(self):
        super().__init__('Invalid Steam profile URL')


class NoBHProfile(CommandInvokeError):
    def __init__(self):
        super().__init__('No Brawlhalla profile exists for that Steam profile')


class NoRankedData(CommandInvokeError):
    def __init__(self):
        super().__init__('There is no ranked data for that Brawlhalla account')


class BrawlhallaCog(Cog):
    @staticmethod
    async def get_bhid(url):
        steamid = await steamapi.url_to_steam_id(url)
        if not steamid:
            raise InvalidURLError
        bhid = await bhapi.search(steamid)
        if not bhid:
            raise NoBHProfile
        return bhid

    @command(name='rank', usage='rank <steam url>')
    async def rank(self, ctx, url):
        bhid = await self.get_bhid(url)
        ranked = await bhapi.player_ranked(bhid)
        if ranked.no_data:
            raise NoRankedData
        return await ctx.send(embed=ranked.to_embed())
