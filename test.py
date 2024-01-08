import os

from db import DBManager
from dotenv import load_dotenv
from telethon import events
from telethon.sync import TelegramClient

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')
phone = '79878783869'
time_sleep = 10

coins = ['XRP/USDT', 'TIA/USDT']

client = TelegramClient('my_session', api_id, api_hash,
                        device_model="iPhone 13 Pro Max",
                        system_version="14.8.1",
                        app_version="8.4",
                        lang_code="en",
                        system_lang_code="en-US"
                        )

db_manager = DBManager()


class FixMessage:
    def __init__(self, id_message):
        self.id_message = id_message

    def check_deal(self):
        deal = db_manager.select_active_message(self.id_message)
        if deal:
            # TODO: API
            db_manager.close_deal(self.id_message)


class CoinMessage:
    def __init__(self, coin, deal_type, message):
        self.coin = coin
        self.deal_type = deal_type
        self.message_id = message['id']

    def save(self):
        db_manager.insert_message(self.message_id, self.coin, self.deal_type)

    def __str__(self):
        return (f'Валюта: {self.coin}\n'
                f'Тип сделки: {self.deal_type}\n'
                f'ID сообщения: {self.message_id}')


def check_coin(message):
    mes_arr = message['message'].split()
    for x, word in enumerate(mes_arr):
        if word == 'Фиксирую':
            return ['fix', message['reply_to']['reply_to_msg_id']]
        if word in coins:
            return ['deal', word, mes_arr[x + 1]]
    return ['']


@client.on(events.NewMessage(chats=('arthur_mukashev')))
async def normal_handler(event):
    mes_dict = event.message.to_dict()
    checked_coin = check_coin(mes_dict)
    if checked_coin[0] == 'fix':
        fix = FixMessage(checked_coin[1])
        fix.check_deal()
    if checked_coin[0] == 'deal':
        coin = CoinMessage(checked_coin[1], 'SHORT' if 'SHORT' in checked_coin[2] else 'LONG', mes_dict)
        coin.save()


client.start()

client.run_until_disconnected()
