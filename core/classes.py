import pprint
from datetime import datetime as dt
import os

import bitget.bitget_api as baseApi
from bitget.exceptions import BitgetAPIException
from dotenv import load_dotenv

from db import DBManager

load_dotenv()

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

productType = "USDT-FUTURES"

db_manager = DBManager()


class FixMessage:
    def __init__(self, id_message):
        self.id_message = id_message
        self.deal = db_manager.select_active_message(self.id_message)

    def check_deal(self):
        if self.deal:
            try:
                api = baseApi.BitgetApi(apiKey, secretKey, passphrase)
                # order = api.get('/api/v2/mix/order/detail', {
                #     'symbol': self.deal[0],
                #     'productType': productType,
                #     'orderId': self.deal[2],
                #     'clientOid': self.deal[3]
                # })

                deal_type = 'SHORT'
                if self.deal[1] == 'BUY':
                    deal_type = 'LONG'

                # TODO: Закрывать сделку правильно
                order = api.get('/api/v2/mix/position/single-position', {
                    'symbol': self.deal[0],
                    'productType': productType,
                    'marginCoin': 'USDT'
                })

                resPost = api.post('/api/v2/mix/order/close-positions', {
                    # Закрывает позицию по рынку
                    "symbol": self.deal[0],
                    "productType": productType,
                    "holdSide": deal_type,
                })
                if resPost['msg'] == 'success':
                    db_manager.close_deal(self.id_message)
                else:
                    # TODO слать сообщение в телеграм
                    print("Не смог закрыть сделку")

                pprint.pprint(order)

            except BitgetAPIException:
                print("error")

    def __str__(self):
        return ''


class CoinMessage:
    def __init__(self, coin, deal_type, deal_max_lever, message):
        self.coin = coin
        self.deal_type = deal_type
        self.deal_max_lever = deal_max_lever
        self.message_id = message['id']

    def save(self):
        clientOid = str(int(dt.timestamp(dt.now()) * 100000))

        try:
            api = baseApi.BitgetApi(apiKey, secretKey, passphrase)

            available_balance = api.get('/api/v2/mix/account/account', {
                'symbol': self.coin,
                'productType': productType,
                'marginCoin': 'usdt'
            })['data']['available']

            balance = float(available_balance) * 0.01

            bidPrice = api.get('/api/v2/mix/market/ticker', {
                'symbol': self.coin,
                'productType': productType,
            })['data'][0]['bidPr']

            size = round((self.deal_max_lever * balance / float(bidPrice)), 7)
            print("size:", size)

            holdSide = 'short'
            if self.deal_type == 'buy':
                holdSide = 'long'

            message_leverage = api.post('/api/v2/mix/account/set-leverage', {
                'symbol': self.coin,
                'productType': productType,
                'marginCoin': 'USDT',
                'leverage': str(self.deal_max_lever),
                'holdSide': holdSide
            })

            if message_leverage['msg'] == 'success':
                resPost = api.post('/api/v2/mix/order/place-order', {
                    "symbol": self.coin,
                    "productType": productType,
                    "marginMode": "crossed",
                    "marginCoin": "USDT",
                    "size": str(size),
                    "side": self.deal_type,  # buy / sell
                    "tradeSide": "open",
                    "orderType": "market",
                    "force": "gtc",
                    "clientOid": clientOid  # придумываем самостоятельно
                })
                if resPost['msg'] == 'success':
                    db_manager.insert_message(self.message_id, self.coin, self.deal_type, resPost['data']['orderId'],
                                              resPost['data']['clientOid'])

        except BitgetAPIException as e:
            print("error:" + e.message)

    def __str__(self):
        return (f'Валюта: {self.coin}\n'
                f'Тип сделки: {self.deal_type}\n'
                f'ID сообщения: {self.message_id}')
