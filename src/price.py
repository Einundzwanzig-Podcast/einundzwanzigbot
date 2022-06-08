from typing import Tuple
import requests
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from database import get_connection
from textwrap import dedent
import os
import config


def get_coinbase_prices():
    """
    Get the current fiat exchange rates for BTC from the Coinbase API
    """
    r = requests.get('https://api.coinbase.com/v2/exchange-rates?currency=BTC', timeout=5)
    json = r.json()
    return json['data']['rates']


def get_last_ath_price_and_message_id() -> Tuple[float, int]:
    """
    Returns the last ATH price with the message id it was sent with
    This message id can then be used to delete the message
    """

    connection = get_connection()
    cur = connection.cursor()

    previous_price = cur.execute('SELECT price_usd, last_message_id FROM price WHERE 1').fetchone()
    connection.close()

    if previous_price == None:
        previous_price = (0.0, 0)

    return previous_price


def save_price_to_db(price: float, last_message_id: int) -> None:
    """
    Saves the new ATH price to the database
    """

    connection = get_connection()
    cur = connection.cursor()

    cur.execute('DELETE FROM price WHERE 1')
    cur.execute('INSERT INTO price (price_usd, last_message_id) VALUES (?, ?)', (price, last_message_id))

    connection.commit()
    connection.close()


def price_update_ath(context: CallbackContext) -> None:
    """
    Gets the current price, compares it to the price in the database and
    sends a message if a new ATH was reached
    """
    try:
        price = float(get_coinbase_prices()['USD'])
    except Exception as e:
        price = 0.0

    (last_ath_price, last_message_id) = get_last_ath_price_and_message_id()

    new_ath = last_ath_price < price

    if not new_ath:
        return
    else:
        price_formatted = '{0:,.2f}'.format(price)

        message = dedent(f"""
        <b>Neues Allzeithoch</b>
        {price_formatted} USD
        """)

        # We try to delete the old message
        # This only works if the message is less than 48 hours old
        try:
            context.bot.delete_message(chat_id=config.FEATURE_ATH_CHAT_ID, message_id=last_message_id)
        except Exception as e:
            pass

        sent_message = context.bot.send_message(text=message, chat_id=config.FEATURE_ATH_CHAT_ID, parse_mode='HTML')

        save_price_to_db(price, sent_message.message_id)


def preis(update: Update, context: CallbackContext):
    """
    Current Coinbase price
    """

    prices = get_coinbase_prices()

    price_usd = float(prices['USD'])
    price_eur = float(prices['EUR'])
    price_chf = float(prices['CHF'])

    message = dedent(f"""
    <b>Preis</b>
    {'{0:,.2f}'.format(price_usd)} USD/BTC
    {'{0:,.2f}'.format(price_eur)} EUR/BTC
    {'{0:,.2f}'.format(price_chf)} CHF/BTC
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def moskauzeit(update: Update, context: CallbackContext):
    """
    Get the current price in satoshi per USD, satoshi per EUR and satoshi per CHF
    """
    prices = get_coinbase_prices()

    price_usd = float(prices['USD'])
    price_eur = float(prices['EUR'])
    price_chf = float(prices['CHF'])

    sat_per_usd = int(1 / price_usd * 100_000_000)
    sat_per_eur = int(1 / price_eur * 100_000_000)
    sat_per_chf = int(1 / price_chf * 100_000_000)

    message = dedent(f"""
    <b>Moskau Zeit</b>
    {sat_per_usd} SAT/USD
    {sat_per_eur} SAT/EUR
    {sat_per_chf} SAT/CHF
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def sat_in_fiat(update: Update, context: CallbackContext):
    """
    Get the current fiat value of your sat amount
    """

    try:
        sats_amount = int(context.args[0])
    except Exception as e:
        sats_amount = 10000

    prices = get_coinbase_prices()

    sats_in_usd = float(prices['USD']) / 100_000_000 * sats_amount
    sats_in_eur = float(prices['EUR']) / 100_000_000 * sats_amount
    sats_in_chf = float(prices['CHF']) / 100_000_000 * sats_amount

    message = dedent(f"""
    {'{0:,.0f}'.format(sats_amount)} sats = {'{0:,.2f}'.format(sats_in_usd)} USD
    {'{0:,.0f}'.format(sats_amount)} sats = {'{0:,.2f}'.format(sats_in_eur)} EUR
    {'{0:,.0f}'.format(sats_amount)} sats = {'{0:,.2f}'.format(sats_in_chf)} CHF
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def glaskugel(update: Update, context: CallbackContext):
    """
    Sends Hosp Meme
    """
    update.message.reply_photo(open(os.path.join(os.path.dirname(__file__), 'img', 'hosp_meme.jpeg'), 'rb'))
