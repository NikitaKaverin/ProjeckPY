import os
import time

import bitget.bitget_api as baseApi
from dotenv import load_dotenv

from db import DBManager

load_dotenv()

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

productType = "USDT-FUTURES"

db_manager = DBManager()

api = baseApi.BitgetApi(apiKey, secretKey, passphrase)

tickers = api.get('/api/v2/mix/market/tickers', {
    'productType': productType
})

for ticker in tickers["data"]:
    time.sleep(0.2)

    coin = db_manager.select_coin(ticker["symbol"])

    if coin:
        continue

    contract = api.get('/api/v2/mix/market/contracts', {
        'productType': productType,
        'symbol': ticker["symbol"]
    })
    db_manager.add_coin(ticker["symbol"], contract["data"][0]["maxLever"])
    print(ticker["symbol"], '-', contract["data"][0]["maxLever"], " - OK")
