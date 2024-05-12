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

from pprint import pprint

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')
phone = '79878783869'
time_sleep = 10
apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

productType = "SUSDT-FUTURES"
marginCoin = "SUSDT"


coin = 'SBTCSUSDT'
deal_type = 'short'

api = baseApi.BitgetApi(apiKey, secretKey, passphrase)
resPost = api.post("/api/v2/mix/order/place-tpsl-order", {
    'marginCoin': marginCoin,
    'productType': productType,
    'symbol': coin,
    'planType': 'profit_plan',
    'triggerPrice': '68800',
    'holdSide': deal_type,
    'size': '0.062'
})
pprint(resPost)


