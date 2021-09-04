import sys
from math import floor, log10

import aiohttp
import regex as re
from discord import Embed

from utils import agree_with_word


class SteamAPI:
    STEAM_URL_REGEX = r'(?:https?:\/\/)?(?:www\.)?steamcommunity\.com\/(?:id\/([^\/ \n]+)|profiles\/([0-9]{17}))'

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def url_to_steam_id(self, url):
        matches = re.match(self.STEAM_URL_REGEX, url)
        if not matches:
            if url.isdigit() and len(url) == 17:
                return int(url)
            return await self.resolve_vanity_url(url)
        if steam_id := matches.group(2):
            return int(steam_id)
        if vanity_url := matches.group(1):
            return await self.resolve_vanity_url(vanity_url)
        return None

    async def resolve_vanity_url(self, vanity_url):
        async with self.session.get('https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/',
                                    params={
                                        'key': self.api_key,
                                        'vanityurl': vanity_url
                                    }) as response:
            res = await response.json()
        if res.get('response', {}).get('success'):
            return res.get('response').get('steamid')
        return None


class BrawlhallaAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = aiohttp.ClientSession()

    async def request(self, method, **kwargs):
        kwargs.update(api_key=self.api_key)
        async with self.session.get(f'https://api.brawlhalla.com/{method}', params=kwargs) as response:
            return await response.json()

    async def search(self, steam_id):
        res = await self.request('search', steamid=steam_id)
        if not res:
            return None
        return res.get('brawlhalla_id')

    async def player_stats(self, bhid):
        return await self.request(f'player/{bhid}/stats')

    async def player_ranked(self, bhid):
        res = await self.request(f'player/{bhid}/ranked')
        return RankedData(res)


class LegendData:
    name: str
    rating: int
    peak_rating: int
    tier: str
    wins: int
    games: int

    def __init__(self, data):
        self.name = data.pop('legend_name_key').title()
        for key in data:
            setattr(self, key, data[key])


class TVTData:
    teamname: str
    rating: int
    peak_rating: int
    tier: str
    wins: int
    games: int
    global_rank: int

    def __init__(self, data):
        for key in data:
            setattr(self, key, data[key])


def get_rating_glory(c1, c2, c3, c4):
    def inner(a):
        return floor(10 * (c1 + (c2 * (a - c3)) / c4))

    return inner


class RankedData:
    no_data: bool
    name: str
    rating: int
    peak_rating: int
    tier: str
    wins: int
    games: int
    region: str
    global_rank: int
    region_rank: int
    legends: list[LegendData]
    tvt: list[TVTData]

    RATING_GLORY_CALULATOR = {
        (0, 1199): lambda _: 250,
        (1200, 1285): get_rating_glory(25, 75, 1200, 86),
        (1286, 1389): get_rating_glory(100, 75, 1286, 104),
        (1390, 1679): get_rating_glory(187, 113, 1390, 290),
        (1680, 1999): get_rating_glory(300, 137, 1680, 320),
        (2000, 2299): get_rating_glory(437, 43, 2000, 300),
        (2300, sys.maxsize): get_rating_glory(480, 1, 2300, 20),
    }

    def __init__(self, data):
        self.no_data = False
        if not data:
            self.no_data = True
            return
        for key in data:
            if not isinstance(data[key], (list, dict)):
                setattr(self, key, data[key])
        self.legends = [LegendData(legend) for legend in data.get('legends')]
        self.tvt = [TVTData(team) for team in data.get('2v2')]

    @property
    def most_played(self) -> LegendData:
        return max(self.legends, key=lambda x: x.games)

    @property
    def highest_ranked(self) -> LegendData:
        return max(self.legends, key=lambda x: x.rating)

    @property
    def total_wins(self):
        return sum([self.wins] + [team.wins for team in self.tvt])

    @property
    def glory(self):
        if (total_wins := self.total_wins) < 10:
            return 0
        rating_glory = 0
        for _range in self.RATING_GLORY_CALULATOR:
            if _range[0] <= self.peak_rating <= _range[1]:
                rating_glory = self.RATING_GLORY_CALULATOR[_range](self.peak_rating)
                break
        if total_wins <= 150:
            return rating_glory + 20 * total_wins
        return rating_glory + 245 + floor(450 * (log10(2 * total_wins) ** 2))

    @property
    def most_played_team(self):
        return max(self.tvt, key=lambda x: x.games)

    def to_embed(self):
        embed = Embed(title='Player ranked data')
        embed.add_field(name='Name', value=f'**{self.name}**')
        embed.add_field(name='Region', value=f'**{self.region}**')
        embed.add_field(name='Legends', value=f'**Highest rating**: {(hr := self.highest_ranked).name} ({hr.rating})\n'
                                              f'**Most played**: {(mp := self.most_played).name} ({mp.games} {agree_with_word(mp.games, "game")})')
        embed.add_field(name='Estimated Glory', value=f'**{self.glory}**', inline=False)
        ovovalue = f'**Rating: {self.tier}** ({self.rating} Elo / {self.peak_rating} Peak)\n' \
                   f'**Games: {self.games}** ' \
                   f'({self.wins} {agree_with_word(self.wins, "win")} / {self.games - self.wins} {agree_with_word(self.games - self.wins, "loss", "losses")})\n' \
                   f'Winrate: {round(self.wins / self.games * 100, 2)}%'
        if self.global_rank:
            ovovalue += f'\n**Global rank: {self.global_rank}**'
        if self.region_rank:
            ovovalue += f'\n**Region rank: {self.region_rank}**'
        embed.add_field(name='1v1', value=ovovalue)
        if not self.tvt:
            tvtvalue = '**No 2v2 teams**'
        else:
            mpt = self.most_played_team
            tvtvalue = f'**Team name: {mpt.teamname}**\n' \
                       f'**Rating: {mpt.tier}** ({mpt.rating} Elo / {mpt.peak_rating} Peak)\n' \
                       f'**Games: {mpt.games}** ' \
                       f'({mpt.wins} {agree_with_word(mpt.wins, "win")} / {mpt.games - mpt.wins} {agree_with_word(mpt.games - mpt.wins, "loss", "losses")})\n' \
                       f'Winrate: {round(mpt.wins / mpt.games * 100, 2)}%'
            if mpt.global_rank:
                tvtvalue += f'\n**Global rank: {mpt.global_rank}**'
        embed.add_field(name='2v2 (most played team)', value=tvtvalue)
        return embed
