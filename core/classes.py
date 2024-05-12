from datetime import datetime as dt
import os

import bitget.bitget_api as baseApi
from dotenv import load_dotenv

from db import DBManager

load_dotenv()

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

test = True

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
                return 1
        return 0

    def get_margin_deal(self, coin):
        available_balance = self.api.get('/api/v2/mix/account/account', {
            'symbol': coin,
            'productType': productType,
            'marginCoin': marginCoin.lower()
        })['data']['available']
        return float(available_balance) * 0.01

    def get_bid_price(self, coin):
        bid_price = self.api.get('/api/v2/mix/market/ticker', {
            'symbol': coin,
            'productType': productType,
        })['data'][0]['bidPr']
        return float(bid_price)

    def set_leverage(self, coin, max_lever, hold_side):
        message_leverage = self.api.post('/api/v2/mix/account/set-leverage', {
            'symbol': coin,
            'productType': productType,
            'marginCoin': marginCoin,
            'leverage': max_lever,
            'holdSide': str(hold_side)
        })
        return message_leverage['msg'] == 'success'

    def place_order(self, coin, size, deal_type):
        client_oid = str(int(dt.timestamp(dt.now()) * 100000))
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
            "clientOid": client_oid  # придумываем самостоятельно
        })
        if res_post['msg'] == 'success':
            return res_post['data']
        return None

    def close_positions(self, coin, hold_side):
        res_post = self.api.post('/api/v2/mix/order/close-positions', {
            # Закрывает позицию по рынку
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

    def place_take_profit(self, coin, hold_side, pl_size):
        res_post = self.api.post("/api/v2/mix/order/place-tpsl-order", {
            'marginCoin': marginCoin,
            'productType': productType,
            'symbol': coin,
            'planType': 'pos_profit',
            'triggerPrice': pl_size,
            'holdSide': hold_side
        })
        return res_post['msg'] == 'success'

    def place_stop_loss(self, coin, hold_side, st_size):
        res_post = self.api.post("/api/v2/mix/order/place-tpsl-order", {
            'marginCoin': marginCoin,
            'productType': productType,
            'symbol': coin,
            'planType': 'pos_loss',
            'triggerPrice': st_size,
            'holdSide': hold_side
        })
        return res_post['msg'] == 'success'


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
            order = self.api.place_order(self.coin, position_size, self.deal_type)
            if order:
                print(f'SUCCESS - Create order in BitGet on coin: {self.coin}')
                db_manager.save_deal(self.message_id, self.coin, self.deal_type, self.hold_side, order['orderId'],
                                     order['clientOid'])
                self.place_tpsl(order)
            else:
                print(f'ERROR - Can\'t place order on coin: {self.coin}')
        else:
            print(f'ERROR - Can\'t set leverage on coin: {self.coin}')

    def place_tpsl(self, order):
        order_detail = self.api.get_order_detail(self.coin, order['orderId'], order['clientOid'])
        quote_volume, leverage, price_avg = float(order_detail['quoteVolume']), float(order_detail['leverage']), float(
            order_detail['priceAvg'])
        percent_pl = ((quote_volume / leverage) * 0.8 / leverage) / (quote_volume / leverage) * 100
        percent_st = ((quote_volume / leverage) * 3 / leverage) / (quote_volume / leverage) * 100

        if order_detail['posSide'] == 'short':
            pl_size = price_avg * (1 - percent_pl / 100)
            st_size = price_avg * (1 + percent_st / 100)
        else:
            pl_size = price_avg * (1 + percent_pl / 100)
            st_size = price_avg * (1 - percent_st / 100)

        self.api.place_take_profit(self.coin, self.hold_side, round(pl_size, 1))
        self.api.place_stop_loss(self.coin, self.hold_side, round(st_size, 1))

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
        if deal_on_bitget == 0:
            db_manager.update_deal_status(self.deal_on_db['id'], 2)
            print(f'SUCCESS - Close deal in DB on coin: {self.deal_on_db['coin']}')
        else:
            if self.api.close_positions(self.deal_on_db['coin'], self.deal_on_db['hold_side']):
                print(f'SUCCESS - Close deal in BitGet on coin: {self.deal_on_db['coin']}')
                db_manager.update_deal_status(self.deal_on_db['id'], 2)
            else:
                print(f'ERROR - Close deal in BitGet on coin: {self.deal_on_db['coin']}')
