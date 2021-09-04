import asyncio
from typing import Union

import aiomysql
from credentials import dev, sql_user, sql_password, sql_host

host = sql_host if dev else '127.0.0.1'
config = {'host': host, 'user': sql_user, 'password': sql_password, 'db': 'prawl', 'autocommit': True}


# noinspection PyGlobalUndefined
async def create_pool():
    global sql_connection_pool
    sql_connection_pool = await aiomysql.create_pool(0, **config)


asyncio.get_event_loop().run_until_complete(create_pool())


async def _abstract_sql(query, *params, fetch=False, fetchall=False, last_row=False) -> Union[list, dict, int, None]:
    async with sql_connection_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(query, params)
            if fetchall:
                return await cur.fetchall()
            elif fetch:
                return await cur.fetchone()
            elif last_row:
                return cur.lastrowid


async def abstract_sql(*args, **kwargs):  # yes that's ugly but sometimes it just dies and i don't want that
    try:
        return await _abstract_sql(*args, **kwargs)
    except (aiomysql.InternalError, BrokenPipeError):
        old_pool = sql_connection_pool
        await create_pool()
        old_pool.close()
        return await _abstract_sql(*args, **kwargs)


async def get_user_link(discord_id):
    res = await abstract_sql('SELECT * FROM `bot_links` WHERE user_id=%s', discord_id, fetch=True)
    if not res:
        return None
    return res.get('brawlhalla_id')


async def update_user_link(discord_id, brawlhalla_id):
    await abstract_sql('INSERT INTO `bot_links` (user_id, brawlhalla_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE brawlhalla_id=%s', discord_id, brawlhalla_id, brawlhalla_id)


async def delete_user_link(discord_id):
    await abstract_sql('DELETE FROM `bot_links` WHERE user_id=%s', discord_id)
