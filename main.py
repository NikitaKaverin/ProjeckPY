import logging
import os

import telegram

from dotenv import load_dotenv
# from telegram import Update
from telethon import TelegramClient, sync, events

load_dotenv()

# Использование переменных в коде
api_id = os.getenv("TELEGRAM_ID")
api_hash = os.getenv("TELEGRAM_HASH")

client = telegram.User(id=5728199654, is_bot=False, first_name='Иван')


print(client.__getstate__())

# client = TelegramClient('session_name', api_id, api_hash)

# client.start()

# for dialog in client.iter_dialogs():
#     print(dialog.title)
