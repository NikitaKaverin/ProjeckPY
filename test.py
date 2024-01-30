from datetime import datetime as dt
import os

import bitget.bitget_api as baseApi
from bitget.exceptions import BitgetAPIException
from dotenv import load_dotenv
from telethon import events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.sync import TelegramClient
from telethon import utils

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')
phone = '79878783869'
time_sleep = 10

client = TelegramClient('my_session', api_id, api_hash,
                        device_model="iPhone 13 Pro Max",
                        system_version="14.8.1",
                        app_version="8.4",
                        lang_code="en",
                        system_lang_code="en-US"
                        )
peer_type = utils.resolve_id(-1001633253042)
print(peer_type)

# async def main():
#     # authentication
#     await client.start(phone)
#
#     # get group and channel list
#     dialogs = await client.get_dialogs()
#
#     # print group and channel data
#     for dialog in dialogs:
#         if dialog.is_group or dialog.is_channel:
#             print(f"{dialog.name}: {dialog.id}")
#
#
# # start
# client.loop.run_until_complete(main())
