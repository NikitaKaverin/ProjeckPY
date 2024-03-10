import time
from pprint import pprint
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

test = False

productType = "USDT-FUTURES"
marginCoin = "USDT"

if test:
    productType = "SUSDT-FUTURES"
    marginCoin = "SUSDT"

db_manager = DBManager()


class FixMessage:
    def __init__(self, id_message):
        self.id_message = id_message
        self.deal = db_manager.select_active_message(self.id_message)

    def check_deal(self):
        if self.deal:
            try:
                api = baseApi.BitgetApi(apiKey, secretKey, passphrase)

                deal_type = 'SHORT'
                if self.deal['deal_type'] == 'BUY':
                    deal_type = 'LONG'

                # TODO: Закрывать сделку правильно
                order = api.get('/api/v2/mix/position/single-position', {
                    'symbol': self.deal['coin'],
                    'productType': productType,
                    'marginCoin': marginCoin
                })

                if order['data']:
                    pnl = float(order['data'][0]['unrealizedPL'])
                    openPrice = float(order["data"][0]["openPriceAvg"])
                    total = float(order["data"][0]["total"])

                    quoteVolume = openPrice * total

                    totalfee = abs((quoteVolume + pnl) / 100 * 0.06) + abs(self.deal['fee'])

                    print(
                        f'Deal: {self.deal['coin']} |\t| '
                        f'quoteVolume = {quoteVolume} |\t| '
                        f'pnl = {pnl} |\t| '
                        f'totalfee = {totalfee} |\t| '
                        f'Close = {pnl > totalfee}')

                    if pnl > totalfee:
                        resPost = api.post('/api/v2/mix/order/close-positions', {
                            # Закрывает позицию по рынку
                            "symbol": self.deal['coin'],
                            "productType": productType,
                            "holdSide": deal_type,
                        })
                        if resPost['msg'] == 'success':
                            db_manager.close_deal(self.id_message, pnl, -totalfee)
                        else:
                            # TODO слать сообщение в телеграм
                            print(f'ERROR Closing Deal: {self.deal["coin"]}')
                        print(f'SUCCESS Closed Deal: {self.deal["coin"]}')
                else:
                    order = api.get('/api/v2/mix/order/orders-history', {
                        'symbol': self.deal['coin'],
                        'productType': productType,
                        # 'orderId': self.deal['orderId']
                    })

                    totalProfits = float(order["data"]["entrustedList"][0]["totalProfits"])
                    fee = float(order["data"]["entrustedList"][0]["fee"])

                    db_manager.manual_close_deal(self.deal['id'], totalProfits, fee)
                    print(f'Manual Close Deal: {self.deal["coin"]}, pnl = {totalProfits}')

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
                'marginCoin': marginCoin.lower()
            })['data']['available']

            balance = float(available_balance) * 0.01

            bidPrice = api.get('/api/v2/mix/market/ticker', {
                'symbol': self.coin,
                'productType': productType,
            })['data'][0]['bidPr']

            size = round((self.deal_max_lever * balance / float(bidPrice)), 7)
            # print("size:", size)

            holdSide = 'short'
            if self.deal_type == 'buy':
                holdSide = 'long'

            message_leverage = api.post('/api/v2/mix/account/set-leverage', {
                'symbol': self.coin,
                'productType': productType,
                'marginCoin': marginCoin,
                'leverage': str(self.deal_max_lever),
                'holdSide': holdSide
            })

            if message_leverage['msg'] == 'success':
                resPost = api.post('/api/v2/mix/order/place-order', {
                    "symbol": self.coin,
                    "productType": productType,
                    "marginMode": "crossed",
                    "marginCoin": marginCoin,
                    "size": str(size),
                    "side": self.deal_type,  # buy / sell
                    "tradeSide": "open",
                    "orderType": "market",
                    "force": "gtc",
                    "clientOid": clientOid  # придумываем самостоятельно
                })
                if resPost['msg'] == 'success':
                    print(f'SUCCESS Create Order: {self.coin}')
                    order = api.get('/api/v2/mix/order/detail', {
                        'symbol': self.coin,
                        'productType': productType,
                        'orderId': resPost['data']['orderId'],
                        'clientOid': resPost['data']['clientOid']
                    })
                    deal = db_manager.select_message(self.coin)
                    if deal and deal['deal_type'] == self.deal_type:
                        fee = abs(deal['fee']) + abs(float(order['data']['fee']))
                        db_manager.update_message(deal['id'], self.message_id, resPost['data']['orderId'],
                                                  resPost['data']['clientOid'], -fee)
                    else:
                        db_manager.insert_message(self.message_id, self.coin, self.deal_type,
                                                  resPost['data']['orderId'],
                                                  resPost['data']['clientOid'], order['data']['fee'])

        except BitgetAPIException as e:
            print("error:" + e.message)

    def __str__(self):
        return (f'Валюта: {self.coin}\n'
                f'Тип сделки: {self.deal_type}\n'
                f'ID сообщения: {self.message_id}')
