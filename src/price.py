from typing import Optional, Tuple
import requests
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from database import get_connection
from textwrap import dedent
import config

def get_coinbase_price(fiat: str = 'USD') -> float:
    """
    Get the current BTC-USD spot exchange rate
    """
    r = requests.get(f'https://api.coinbase.com/v2/prices/spot?currency={fiat}')
    json = r.json()
    return float(json['data']['amount'])

def save_price_to_db(price: float) -> bool:
 
    connection = get_connection()
    cur = connection.cursor()

    previous_price = cur.execute('SELECT price_usd FROM price WHERE 1').fetchone()

    if previous_price == None:
        previous_price = 0.0
    else:
        previous_price = previous_price[0]

    if previous_price >= price:
        connection.close()
        return False
    else:
        cur.execute('DELETE FROM price WHERE 1')
        cur.execute('INSERT INTO price (price_usd) VALUES (?)', (price,))

        connection.commit()
        connection.close()

        return True

def price_update_ath(context: CallbackContext) -> None:
    """
    Gets the current price, compares it to the price in the database and
    sends a message if a new ATH was reached
    """
    price = get_coinbase_price()
    new_ath = save_price_to_db(price)

    price_formatted = '{0:,.2f}'.format(price)

    if new_ath:
        message = dedent(f"""
        <b>Neues Allzeithoch</b>
        {price_formatted} USD
        """)
        context.bot.send_message(text=message, chat_id=config.EINUNDZWANZIG_CHAT_ID, parse_mode='HTML')

def moskauzeit(update: Update, _: CallbackContext):
    """
    Get the current price in satoshi per USD and satoshi per EUR
    """
    price_usd = get_coinbase_price('USD')
    price_eur = get_coinbase_price('EUR')

    sat_per_usd = int(1 / price_usd * 100_000_000)
    sat_per_eur = int(1 / price_eur * 100_000_000)

    message = dedent(f"""
    <b>Moskau Zeit</b>
    {sat_per_usd} SAT/USD
    {sat_per_eur} SAT/EUR
    """)
    update.message.reply_text(text=message, parse_mode='HTML')

