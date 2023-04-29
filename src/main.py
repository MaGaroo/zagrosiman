import asyncio
import datetime
import time

import socks
from telethon import TelegramClient, events

from messages import (
    ALREADY_RESERVED,
    CANCEL,
    CHOOSE_DATE_MESSAGE,
    DOUBLE_CHECK_KEYWORD,
    RESERVE,
    RESERVE_FAILED,
    RESERVE_SUCCESSFUL,
    SILENCE,
    YES,
)
from settings import API_HASH, API_ID, MY_USERNAME, SEATS, SESSION
from status import Status

BOT = "zagrosibot"


reserved = {}
status = Status()

client = TelegramClient(
    SESSION, API_ID, API_HASH, proxy=(socks.SOCKS5, "localhost", 1080, True)
)
client.start()


@client.on(events.NewMessage(chats=["zagrosibot"]))
async def handle_choose_date(e):
    if DOUBLE_CHECK_KEYWORD in e.raw_text:
        msg = e.message
        buttons = await msg.get_buttons()
        await buttons[0][0].click()
        return
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


@client.on(events.NewMessage(chats=["zagrosibot"]))
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
            await client.send_message(MY_USERNAME, f"{date} >>>> {i}")
            return

    status.reserving = False
    reserved[date] = True
    await client.send_message(MY_USERNAME, date + " نشد")


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
