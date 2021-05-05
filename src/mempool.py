import requests
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from textwrap import dedent
import config

class MempoolSpaceFees:
    def __init__(self, one_block_fee: int, three_block_fee: int, six_block_fee: int) -> None:
        self.one_block_fee = one_block_fee
        self.three_block_fee = three_block_fee
        self.six_block_fee = six_block_fee

def mempool_space_fees(update: Update, _: CallbackContext):
    """
    Recommended fees from mempool space
    """
    r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/fees/recommended')
    json = r.json()

    fees = MempoolSpaceFees(
        one_block_fee=json['fastestFee'],
        three_block_fee=json['halfHourFee'],
        six_block_fee=json['hourFee']
    )

    message = dedent(f"""
    <b>Gebühren</b>
    Ein Block (10 min): {fees.one_block_fee} sat/vbyte
    Drei Blöcke (30 min): {fees.three_block_fee} sat/vbyte
    Sechs Blöcke (60 min): {fees.six_block_fee} sat/vbyte
    """)

    update.message.reply_text(message, parse_mode='HTML')

def blockzeit(update: Update, _: CallbackContext):
    """
    Returns the current block time (block height)
    """
    r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/blocks/tip/height')
    height = r.json()

    message = dedent(f"""
    <b>Aktuelle Blockzeit</b>
    {height}
    """)

    update.message.reply_text(message, parse_mode='HTML')
