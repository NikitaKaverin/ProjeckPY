import os

from dotenv import load_dotenv
from telethon import events
from telethon.sync import TelegramClient

from db import DBManager

from core.classes import FixMessage, CoinMessage

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')
phone = '79878783869'
time_sleep = 10

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

productType = "USDT-FUTURES"

# Original
# chat_id = 1633253042

# VIP
chat_id = 1781065102

# TEST
# chat_id = 1489990553

db_manager = DBManager()

client = TelegramClient('my_session', api_id, api_hash,
                        device_model="iPhone 14 Pro Max",
                        system_version="17.0.1",
                        app_version="8.4",
                        lang_code="en",
                        system_lang_code="en-US"
                        )


def check_message(message):
    mes_arr = message['message'].split()

    if message['reply_to'] is not None:
        return ['fix', message['reply_to']['reply_to_msg_id']]

    for x, word in enumerate(mes_arr):
        coin = db_manager.select_coin(word.replace("/", ""))
        if coin:
            return ['deal', coin[0], mes_arr[x + 1], coin[1]]
    return ['']


@client.on(events.NewMessage(chats=[chat_id]))
async def normal_handler(event):
    mes_dict = event.message.to_dict()
    checked_message = check_message(mes_dict)
    if checked_message[0] == 'fix':
        fix = FixMessage(checked_message[1])
        fix.check_deal()
    elif checked_message[0] == 'deal':
        coin = CoinMessage(checked_message[1], 'SELL' if 'SHORT' in checked_message[2] else 'BUY', checked_message[3],
                           mes_dict)
        coin.save()
    else:
        print("Монеты нет в базе. Запустите refresh_coins.py")


client.start()

client.run_until_disconnected()
