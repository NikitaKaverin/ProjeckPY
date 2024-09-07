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
marginDealPercentage = float(os.getenv('MARGIN_DEAL_PERCENTAGE'))
takeProfitPercentage = float(os.getenv('TAKE_PROFIT_PERCENTAGE'))
stopLossPercentage = float(os.getenv('STOP_LOSS_PERCENTAGE'))


test = False

productType = "USDT-FUTURES"
marginCoin = "USDT"

if test:
    productType = "SUSDT-FUTURES"
    marginCoin = "SUSDT"

db_manager = DBManager()


class MyAPI:
    def __init__(self, apiKey, secretKey, passphrase):
        self.api = baseApi.BitgetApi(apiKey, secretKey, passphrase)

    def get_single_position(self, symbol, deal_type):
        pos = self.api.get("/api/v2/mix/position/single-position", {
            'productType': productType,
            'marginCoin': marginCoin,
            'symbol': symbol
        })
        deals = pos['data']
        for deal in deals:
            if deal['holdSide'] == deal_type.lower():
                return {'exist': 1, 'pnl': float(deal['unrealizedPL'])}
        return {'exist': 0}

    def get_margin_deal(self, coin):
        available_balance = self.api.get('/api/v2/mix/account/account', {
            'symbol': coin,
            'productType': productType,
            'marginCoin': marginCoin.lower()
        })['data']['available']
        return float(available_balance) * marginDealPercentage

    def get_bid_price(self, coin):
        bid_price = self.api.get('/api/v2/mix/market/ticker', {
            'symbol': coin,
            'productType': productType,
        })['data'][0]['bidPr']
        return float(bid_price)

    def set_leverage(self, coin, max_lever, hold_side):
        try:
            message_leverage = self.api.post('/api/v2/mix/account/set-leverage', {
                'symbol': coin,
                'productType': productType,
                'marginCoin': marginCoin,
                'leverage': max_lever,
                'holdSide': str(hold_side)
            })
        except BitgetAPIException as e:
            max_lever = e.message[-2:]
            self.api.post('/api/v2/mix/account/set-leverage', {
                'symbol': coin,
                'productType': productType,
                'marginCoin': marginCoin,
                'leverage': int(max_lever),
                'holdSide': str(hold_side)
            })
            return True
        return message_leverage['msg'] == 'success'

    def place_order(self, coin, size, deal_type, leverage, bid_price):
        client_oid = str(int(dt.timestamp(dt.now()) * 100000))

        percent_pl = ((size / leverage) * takeProfitPercentage / leverage) / (size / leverage) * 100
        percent_st = ((size / leverage) * stopLossPercentage / leverage) / (size / leverage) * 100

        if deal_type.lower() == 'sell':
            pl_size = round(bid_price * (1 - percent_pl / 100), 1)
            st_size = round(bid_price * (1 + percent_st / 100), 1)
        else:
            pl_size = round(bid_price * (1 + percent_pl / 100), 1)
            st_size = round(bid_price * (1 - percent_st / 100), 1)

        # Установить сделку
        res_post = self.api.post('/api/v2/mix/order/place-order', {
            "symbol": coin,
            "productType": productType,
            "marginMode": "crossed",
            "marginCoin": marginCoin,
            "size": str(size),
            "side": deal_type,  # buy / sell
            "tradeSide": "open",
            "orderType": "market",
            "force": "gtc",
            "presetStopSurplusPrice": pl_size,
            "presetStopLossPrice": st_size,
            "clientOid": client_oid  # придумываем самостоятельно
        })
        if res_post['msg'] == 'success':
            return res_post['data']
        return None

    def close_positions(self, coin, hold_side):
        # Закрывает позицию по рынку
        res_post = self.api.post('/api/v2/mix/order/close-positions', {
            "symbol": coin,
            "productType": productType,
            "holdSide": hold_side,
        })
        return res_post['msg'] == 'success'

    def get_order_detail(self, coin, order_id, client_oid):
        order = self.api.get('/api/v2/mix/order/detail', {
            'symbol': coin,
            'productType': productType,
            'orderId': order_id,
            'clientOid': client_oid
        })
        return order['data']


class DealMessage:
    def __init__(self, message):
        self.coin = message['coin']
        self.deal_type = message['deal_type']  # buy / sell
        self.hold_side = message['hold_side']  # long / short
        self.deal_max_lever = message['maxLever']
        self.message_id = message['msg_id']
        self.deal_on_bitget = message['deal_on_bitget']
        self.deal_on_db = message['deal_on_db']
        self.api = MyAPI(apiKey, secretKey, passphrase)

    def decide(self):
        if self.deal_on_db == 0 and self.deal_on_bitget == 0:
            self.create_deal_api_and_db()
        if self.deal_on_db == 1 and self.deal_on_bitget == 0:
            active_deal = db_manager.get_active_deal(self.coin, self.deal_type)
            db_manager.update_deal_status(active_deal['id'], 2)
            self.create_deal_api_and_db()

    def create_deal_api_and_db(self):
        if self.api.set_leverage(self.coin, self.deal_max_lever, self.hold_side):
            margin_deal = self.api.get_margin_deal(self.coin)
            bid_price = self.api.get_bid_price(self.coin)
            position_size = round((self.deal_max_lever * margin_deal / bid_price), 7)
            order = self.api.place_order(self.coin, position_size, self.deal_type, self.deal_max_lever, bid_price)
            if order:
                print(f'SUCCESS - Create order in BitGet on coin: {self.coin}')
                db_manager.save_deal(self.message_id, self.coin, self.deal_type, self.hold_side, order['orderId'],
                                     order['clientOid'])
            else:
                print(f'ERROR - Can\'t place order on coin: {self.coin}')
        else:
            print(f'ERROR - Can\'t set leverage on coin: {self.coin}')

    @staticmethod
    def select_coin(coin):
        return db_manager.select_coin(coin)

    @staticmethod
    def check_exist_deal(coin, deal_type):
        active_deal = db_manager.check_active_deal(coin, deal_type)
        if active_deal:
            return active_deal['flag']
        else:
            return 0


class DealFixMessage:
    def __init__(self, message):
        self.deal_on_db = db_manager.get_deal_by_msg_id(message['reply_id'])
        self.api = MyAPI(apiKey, secretKey, passphrase)

    def decide(self):
        deal_on_bitget = self.api.get_single_position(self.deal_on_db['coin'], self.deal_on_db['hold_side'])
        if deal_on_bitget['exist'] == 0:
            db_manager.update_deal_status(self.deal_on_db['id'], 2)
            print(f'SUCCESS - Close deal in DB on coin: {self.deal_on_db["coin"]}')
        else:
            if deal_on_bitget['pnl'] > 0:
                if self.api.close_positions(self.deal_on_db["coin"], self.deal_on_db["hold_side"]):
                    print(f'SUCCESS - Close deal in BitGet on coin: {self.deal_on_db["coin"]}')
                    db_manager.update_deal_status(self.deal_on_db["id"], 2)
                else:
                    print(f'ERROR - Close deal in BitGet on coin: {self.deal_on_db["coin"]}')
            print(f'ERROR - PNL < 0 in BitGet on coin: {self.deal_on_db["coin"]}')
