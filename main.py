import os
import json
import warnings

import telethon.types
from dotenv import load_dotenv
from telethon import events
from telethon.sync import TelegramClient

from core.classes import MyAPI, DealMessage, DealFixMessage

warnings.filterwarnings("ignore")

load_dotenv()
api_id = int(os.getenv('TELEGRAM_ID'))
api_hash = os.getenv('TELEGRAM_HASH')

apiKey = os.getenv('BITGET_API_KEY')
secretKey = os.getenv('BITGET_SECRET_KEY')
passphrase = os.getenv('BITGET_PASSPHRASE')

# Original
# chat_id = 1633253042

# VIP
# chat_id = 1781065102

# TEST
chat_id = 1489990553

# Check_Chat
check_chat_id = 4282973738

api_manager = MyAPI(apiKey, secretKey, passphrase)

client = TelegramClient('my_session', api_id, api_hash,
                        device_model="iPhone 14 Pro Max",
                        system_version="17.0.1",
                        app_version="8.4",
                        lang_code="en",
                        system_lang_code="en-US"
                        )


def check_message(msg):
    if msg.reply_to:
        return {
            'type': 'fix',
            'reply_id': msg.reply_to.reply_to_msg_id
        }

    if 'СПОТ' in msg.message:
        return {
            'type': 'spot'
        }

    msg_arr = msg.message.split()
    db_coin = DealMessage.select_coin(msg_arr[0].replace("/", ""))

    if db_coin:
        if 'LON' in msg.message:
            hold_side = "LONG"
            msg_deal_type = "BUY"
        else:
            hold_side = "SHORT"
            msg_deal_type = "SELL"

        client.send_message(check_chat_id, msg.message)

        deal_on_bitget = api_manager.get_single_position(db_coin['name'], hold_side)['exist']
        deal_on_db = DealMessage.check_exist_deal(db_coin['name'], msg_deal_type)

        if (deal_on_db == 1 and deal_on_bitget == 1) or (deal_on_db == 0 and deal_on_bitget == 1):
            return {
                'type': 'nothing'
            }

        return {
            'type': 'deal',
            'coin': db_coin['name'],
            'hold_side': hold_side.lower(),
            'deal_type': msg_deal_type,
            'maxLever': db_coin['maxLever'],
            'msg_id': msg.id,
            'deal_on_db': deal_on_db,
            'deal_on_bitget': deal_on_bitget
        }

    return {
        'type': 'comment'
    }


@client.on(events.NewMessage(chats=[chat_id]))
async def normal_handler(event):
    checked_message = check_message(event.message)
    msg_type = checked_message['type']
    await client.send_message(telethon.types.PeerChat(check_chat_id), json.dumps(checked_message))
    if msg_type == 'deal':
        deal = DealMessage(checked_message)
        deal.decide()
    elif msg_type == 'fix':
        fix = DealFixMessage(checked_message)
        if fix.deal_on_db:
            fix.decide()
    else:
        print()


client.start()

client.run_until_disconnected()
