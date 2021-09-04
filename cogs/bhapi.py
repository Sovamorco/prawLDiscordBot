import inspect

from discord.ext.commands import Cog, command, MissingRequiredArgument

from dblink import *
from general import *


class NoBHProfile(CommandInvokeError):
    def __init__(self):
        super().__init__('No Brawlhalla profile exists for that Steam profile')


class NoRankedData(CommandInvokeError):
    def __init__(self):
        super().__init__('There is no ranked data for that Brawlhalla account')


class InvalidNameError(CommandInvokeError):
    def __init__(self):
        super().__init__('Invalid Steam name')


class NoError(CommandInvokeError):
    def __init__(self):
        super().__init__('')


class BrawlhallaCog(Cog):
    @staticmethod
    async def choose_name(ctx, name):
        players = await bhapi.search_name(name)
        if not players:
            raise InvalidNameError
        if len(players) == 1:
            return players[0].brawlhalla_id

        players = players[:10]
        desc = '\n'.join([f'**{i + 1}.** {player.name} ({player.region}, {player.rating} Elo)' for i, player in enumerate(players)])
        embed = Embed(title='Choose a player', description=desc)
        embed.set_footer(text='Type 0 to cancel. Automatically cancels after 60 seconds.')
        msg = await ctx.send(embed=embed)

        def validate(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.isdigit() and len(players) >= int(m.content) >= 0

        try:
            res = await prawl.wait_for('message', check=validate, timeout=60)
        except asyncio.TimeoutError:
            raise NoError
        finally:
            await msg.delete()
        if res.content == '0':
            raise NoError
        return players[int(res.content) - 1].brawlhalla_id

    async def get_bhid(self, ctx, name):
        steamid = await steamapi.url_to_steam_id(name)
        if steamid:
            bhid = await bhapi.search(steamid)
        else:
            bhid = await self.choose_name(ctx, name)
        if not bhid:
            raise NoBHProfile
        return bhid

    @command(name='rank', usage='rank [steam url or name]')
    async def rank(self, ctx, *, name=None):
        if not name:
            bhid = await get_user_link(ctx.author.id)
            if not bhid:
                raise MissingRequiredArgument(inspect.Parameter('name', 3))
        else:
            bhid = await self.get_bhid(ctx, name)
        ranked = await bhapi.player_ranked(bhid)
        if ranked.no_data:
            raise NoRankedData
        return await ctx.send(embed=ranked.to_embed())

    @command(name='link', usage='link <steam url or name>')
    async def link(self, ctx, *, name):
        bhid = await self.get_bhid(ctx, name)
        await update_user_link(ctx.author.id, bhid)
        await ctx.message.add_reaction('👌')

    @command(name='unlink')
    async def unlink(self, ctx):
        if not await get_user_link(ctx.author.id):
            return await ctx.send('No account linked')
        await delete_user_link(ctx.author.id)
        await ctx.message.add_reaction('👌')
