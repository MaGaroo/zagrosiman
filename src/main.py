import asyncio
import socks
from telethon import TelegramClient, events
import time
import datetime

from messages import (
    ALREADY_RESERVED,
    CANCEL,
    CHOOSE_DATE_MESSAGE,
    RESERVE,
    RESERVE_FAILED,
    RESERVE_SUCCESSFUL,
    SILENCE,
    YES,
)
from status import Status
from settings import API_ID, API_HASH, SESSION, SEATS


BOT = "zagrosibot"


reserved = {}
status = Status()

client = TelegramClient(
    SESSION,
    API_ID,
    API_HASH,
    proxy=(socks.SOCKS5, "localhost", 1080, True)
)
client.start()


@client.on(events.NewMessage(chats=["zagrosibot"]))
async def handle_choose_date(e):
    if status.reserving:
        return
    if e.raw_text == CHOOSE_DATE_MESSAGE:
        msg = e.message
        buttons = await msg.get_buttons()
        if not buttons:
            return
        new_reserved = False
        for row in buttons:
            for btn in row:
                date = btn.text
                if not reserved.get(date, False):
                    await client.send_message(BOT, CANCEL)
                    await reserve(date)
                    new_reserved = True
        if not new_reserved:
            await asyncio.sleep(get_sleep_time())
        await send_reserve_request()


@client.on(events.NewMessage)
async def reserve_response_handler(e):
    if e.raw_text in [RESERVE_SUCCESSFUL, ALREADY_RESERVED]:
        status.ok = True
        status.ready = True
    if e.raw_text == RESERVE_FAILED:
        status.ok = False
        status.ready = True


async def reserve(date):
    status.reserving = True
    for i in SEATS:
        status.ready = False
        status.ok = False
        await client.send_message(BOT, RESERVE)
        await client.send_message(BOT, date)
        await client.send_message(BOT, SILENCE)
        await client.send_message(BOT, str(i))
        await client.send_message(BOT, YES)
        while not status.ready:
            await asyncio.sleep(0.1)
        if status.ok:
            reserved[date] = True
            status.reserving = False
            await client.send_message("MaGaroo", f"{date} >>>> {i}")
            return

    status.reserving = False
    reserved[date] = True
    await client.send_message("MaGaroo", date + " نشد")


async def send_reserve_request():
    await client.send_message(BOT, CANCEL)
    await client.send_message(BOT, CANCEL)
    await client.send_message(BOT, CANCEL)
    await client.send_message(BOT, RESERVE)


def get_sleep_time():
    now = datetime.datetime.now().time()

    if now < datetime.time(0, 30):
        return 10
    if now > datetime.time(23, 30):
        return 10

    return 15 * 60


client.run_until_disconnected()