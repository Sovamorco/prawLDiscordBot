from credentials import brawlhalla_api_key, steam_api_key
from discord.ext.commands import Bot, when_mentioned_or

from brawlhalla import BrawlhallaAPI, SteamAPI
from utils import all_casings

prawl = Bot(when_mentioned_or(*all_casings('prr ')), case_insensitive=True)
prawl.remove_command('help')

bhapi = BrawlhallaAPI(brawlhalla_api_key)
steamapi = SteamAPI(steam_api_key)
