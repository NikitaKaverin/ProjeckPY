from datetime import datetime as dt
import os

import bitget.bitget_api as baseApi
from bitget.exceptions import BitgetAPIException
from dotenv import load_dotenv
from telethon import events
from telethon.sync import TelegramClient

from db import DBManager

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')
phone = '79878783869'
time_sleep = 10

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

productType = "USDT-FUTURES"

chat_id = 1633253042
# chat_id = 1489990553

coins = ["BTC/USDT", "ETH/USDT", "SUI/USDT", "MANTA/USDT", "SOL/USDT", "ZRX/USDT", "AVAX/USDT", "UMA/USDT", 'XRP/USDT',
         '1000SATS/USDT', "XAI/USDT", "CHZ/USDT", "MATIC/USDT", "NEAR/USDT", "ETC/USDT",
         "SEI/USDT", "STORJ/USDT", "APT/USDT", "ICP/USDT", "LINK/USDT", "ARB/USDT", "BCH/USDT", "INJ/USDT",
         "BIGTIME/USDT", "BLUR/USDT", "FTM/USDT", "ADA/USDT", "ORDI/USDT", "DOGE/USDT", "ENS/USDT", "PEOPLE/USDT",
         "MAGIC/USDT", "OP/USDT", "BNB/USDT", "ACE/USDT", "STX/USDT", "PEPE/USDT", "DYDX/USDT", "ALPHA/USDT",
         "AXS/USDT", "IOTA/USDT", "LTC/USDT", "PENDLE/USDT", "DOT/USDT", "EOS/USDT", "RND/USDT", "LUNA2/USDT",
         "ASTR/USDT", "JTO/USDT", "WLD/USDT", "MAV/USDT", "PYTH/USDT", "BAND/USDT", "FIL/USDT", "BSV/USDT", "TRX/USDT",
         "ATOM/USDT", "RAD/USDT", "LUNC/USDT", "MKR/USDT", "CELO/USDT", "SAND/USDT", "IMX/USDT", "LDO/USDT",
         "WOO/USDT", "CRV/USDT", "GALA/USDT", "EGLD/USDT", "RUNE/USDT", "SHIB/USDT", "AAVE/USDT", "FET/USDT",
         "COMP/USDT", "APE/USDT", "MANA/USDT", "MINA/USDT", "MASK/USDT", "1INCH/USDT", "UNI/USDT", "BAKE/USDT",
         "KAVA/USDT", "GRT/USDT", "KLAY/USDT", "SKL/USDT", "THETA/USDT", "KSM/USDT", "WAVES/USDT", "ZIL/USDT",
         "ENJ/USDT", "SUSHI/USDT", "GAL/USDT", "GTC/USDT", 'TIA/USDT', 'LOOM/USDT', 'ORBS/USDT', 'WAXP/USDT',
         'POLYX/USDT', 'TWT/USDT', 'MEME/USDT', '1000RATS/USDT', 'XLM/USDT', 'XTZ/USDT', 'DASH/USDT']

# coins = ["SXRP/SUSDT", "SBTC/SUSDT"]

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
        hold = db_manager.select_active_hold(self.id_message)

        if deal:
            coin = deal[0]
            deal_type = hold[0]

            if deal_type == 'SELL':
                deal_type = 'SHORT'
            else:
                deal_type = 'LONG'

            try:
                api = baseApi.BitgetApi(apiKey, secretKey, passphrase)
                resPost = api.post('/api/v2/mix/order/close-positions', {
                    # Закрывает позицию по рынку
                    "symbol": coin,
                    "productType": productType,
                    "holdSide": deal_type,
                })
                if resPost['msg'] == 'success':
                    db_manager.close_deal(self.id_message)
                else:
                    # TODO слать сообщение в телеграм
                    print("Не смог закрыть сделку")

            except BitgetAPIException as e:
                print("error:" + e.message)
        else:
            del self


class CoinMessage:
    def __init__(self, coin, deal_type, message):
        self.coin = coin.replace('/', '')
        self.deal_type = deal_type
        self.message_id = message['id']

    def save(self):
        clientOid = str(int(dt.timestamp(dt.now()) * 100000))

        try:
            api = baseApi.BitgetApi(apiKey, secretKey, passphrase)
            bidPrice = api.get('/api/v2/mix/market/ticker', {
                'symbol': self.coin,
                'productType': productType,
            })['data'][0]['bidPr']
            print(bidPrice)
            size = round(10 / float(bidPrice) * 10, 7)

            resPost = api.post('/api/v2/mix/order/place-order', {
                "symbol": self.coin,
                "productType": productType,
                "marginMode": "isolated",
                "marginCoin": "USDT",
                "size": str(size),
                "side": self.deal_type,  # buy / sell
                "tradeSide": "open",
                "orderType": "market",
                "force": "gtc",
                "clientOid": clientOid  # придумываем самостоятельно
            })
            if resPost['msg'] == 'success':
                db_manager.insert_message(self.message_id, self.coin, self.deal_type)
            else:
                del self

        except BitgetAPIException as e:
            print("error:" + e.message)

    def __str__(self):
        return (f'Валюта: {self.coin}\n'
                f'Тип сделки: {self.deal_type}\n'
                f'ID сообщения: {self.message_id}')


def check_coin(message):
    mes_arr = message['message'].split()
    for x, word in enumerate(mes_arr):
        if word == 'Фиксирую' and message['reply_to'] is not None:
            return ['fix', message['reply_to']['reply_to_msg_id']]
        if word in coins:
            return ['deal', word, mes_arr[x + 1]]
    return ['']


@client.on(events.NewMessage(chats=[chat_id]))
async def normal_handler(event):
    mes_dict = event.message.to_dict()
    checked_coin = check_coin(mes_dict)
    if checked_coin[0] == 'fix':
        fix = FixMessage(checked_coin[1])
        fix.check_deal()
    if checked_coin[0] == 'deal':
        coin = CoinMessage(checked_coin[1], 'SELL' if 'SHORT' in checked_coin[2] else 'BUY', mes_dict)
        coin.save()


client.start()

client.run_until_disconnected()
