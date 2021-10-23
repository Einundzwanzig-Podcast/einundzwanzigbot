import logging
from textwrap import dedent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

import config

from database import setup_database
from taproot import taproot_handle_command
from mempool import blockzeit, mempool_space_mempool_stats, mempool_space_fees, halving
from price import glaskugel, moskauzeit, preis, price_update_ath, sat_in_fiat
from einundzwanzig import episode, shoutout, memo, invoice, cancel, SHOUTOUT_AMOUNT, SHOUTOUT_MEMO, soundboard, \
    soundboard_button


def start_command(update: Update, context: CallbackContext):
    """
    Sends a welcome message to the user
    Should be customized in the future
    """

    welcome_message = dedent("""
    Hi, ich bin der Einundzwanzig Bot, der offizielle Telegram Bot des Einundzwanzig Bitcoin Podcasts.

    Du findest den Podcast bei allen gängigen Podcast Apps, oder unter https://einundzwanzig.space.

    Kommandos:
    /taproot - Zeit bis zur Aktivierung von Taproot.
    /fee - Aktuelle Transaktionsgebühren.
    /mempool - Mempool Visualisierung. Ersters Argument ist die Zahl der Mempool Blöcke, max <i>8</i>.
    /preis - Preis in USD, EUR und CHF.
    /halving - Zeit bis zum nächsten Halving.
    /satineur - <i>satoshis</i> Gibt den EUR Preis der satoshis an.
    /satinusd - <i>satoshis</i> Gibt den USD Preis der satoshis an.
    /satinchf - <i>satoshis</i> Gibt den CHF Preis der satoshis an.
    /blockzeit - Aktuelle Blockzeit.
    /moskauzeit - SAT per USD, SAT per EUR und SAT per CHF.
    /episode - <i>typ</i> Link zu der letzten Podcast Episode (Alle, Interviews, Lesestunde, News, Weg)
    /shoutout - LN Invoice für einen Shoutout (Ab 21000 sats vorgelesen im Podcast)
    /glaskugel - Preis Vorhersage
    /soundboard - Sound Auswahl als Sprachnachricht
    """)

    update.message.reply_text(text=welcome_message, parse_mode='HTML', disable_web_page_preview=True)


def taproot_command(update: Update, context: CallbackContext):
    """
    Calculates Taproot Activation Statistics
    """
    taproot_handle_command(update, context)


def fee_command(update: Update, context: CallbackContext):
    """
    Get fees for next blocks from mempool.space
    """
    mempool_space_fees(update, context)


def mempool_command(update: Update, context: CallbackContext):
    """
    Get current mempool stats
    """
    mempool_space_mempool_stats(update, context)


def blockzeit_command(update: Update, context: CallbackContext):
    """
    Get the current block time (block height)
    """
    blockzeit(update, context)


def preis_command(update: Update, context: CallbackContext):
    """
    Get the current price in USD, EUR and CHF
    """
    preis(update, context)


def halving_command(update: Update, context: CallbackContext):
    """
    Get the time until the next halving
    """
    halving(update, context)


def moskauzeit_command(update: Update, context: CallbackContext):
    """
    Get the current moscow time (sat/USD, sat/EUR and sat/CHF)
    """
    moskauzeit(update, context)


def sat_in_eur_command(update: Update, context: CallbackContext):
    """
    Get the current EUR value of your sat amount
    """
    sat_in_fiat(update, context, fiat='EUR')


def sat_in_usd_command(update: Update, context: CallbackContext):
    """
    Get the current USD value of your sat amount
    """
    sat_in_fiat(update, context, fiat='USD')

def sat_in_chf_command(update: Update, context: CallbackContext):
    """
    Get the current CHF value of your sat amount
    """
    sat_in_fiat(update, context, fiat='CHF')

def episode_command(update: Update, context: CallbackContext):
    """
    Get the most recent podcast episode
    """
    episode(update, context)


def shoutout_command(update: Update, context: CallbackContext) -> int:
    """
    Returns a TallyCoin LN invoice for a specific amount that includes a memo
    """
    return shoutout(update, context)


def memo_command(update: Update, context: CallbackContext) -> int:
    """
    Returns a TallyCoin LN invoice for a specific amount that includes a memo
    """
    return memo(update, context)


def invoice_command(update: Update, context: CallbackContext) -> int:
    """
    Returns a TallyCoin LN invoice for a specific amount that includes a memo
    """
    return invoice(update, context)


def cancel_command(update: Update, context: CallbackContext) -> int:
    """
    Returns a TallyCoin LN invoice for a specific amount that includes a memo
    """
    return cancel(update, context)


def glaskugel_command(update: Update, context: CallbackContext):
    """
    Sends the Hosp Glaskugel picture
    """
    glaskugel(update, context)


def soundboard_command(update: Update, context: CallbackContext):
    """
    Sends back a markup of soundboard files
    """
    soundboard(update, context)


def run(bot_token: str):
    """
    Starts the bot
    """

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    setup_database()

    updater = Updater(token=bot_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start_command, run_async=True)
    taproot_handler = CommandHandler('taproot', taproot_command, run_async=True)
    fee_handler = CommandHandler('fee', fee_command, run_async=True)
    mempool_handler = CommandHandler('mempool', mempool_command, run_async=True)
    preis_handler = CommandHandler('preis', preis_command, run_async=True)
    halving_handler = CommandHandler('halving', halving_command, run_async=True)
    sat_in_eur_handler = CommandHandler('satineur', sat_in_eur_command, run_async=True)
    sat_in_usd_handler = CommandHandler('satinusd', sat_in_usd_command, run_async=True)
    sat_in_chf_handler = CommandHandler('satinchf', sat_in_chf_command, run_async=True)
    blockzeit_handler = CommandHandler('blockzeit', blockzeit_command, run_async=True)
    moskauzeit_handler = CommandHandler('moskauzeit', moskauzeit_command, run_async=True)
    episode_handler = CommandHandler('episode', episode_command, run_async=True)
    shoutout_handler = ConversationHandler(
        entry_points=[CommandHandler('shoutout', shoutout_command)],
        states={
            SHOUTOUT_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, memo_command)],
            SHOUTOUT_MEMO: [MessageHandler(Filters.text & ~Filters.command, invoice_command)]
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
        run_async=True,
        allow_reentry=True,
        conversation_timeout=60 * 20,  # 20 minutes
        name='shoutout'
    )
    glaskugel_handler = CommandHandler('glaskugel', glaskugel_command, run_async=True)
    soundboard_handler = CommandHandler('soundboard', soundboard_command, run_async=True)
    soundboard_callback_handler = CallbackQueryHandler(soundboard_button)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(taproot_handler)
    dispatcher.add_handler(fee_handler)
    dispatcher.add_handler(mempool_handler)
    dispatcher.add_handler(preis_handler)
    dispatcher.add_handler(halving_handler)
    dispatcher.add_handler(sat_in_eur_handler)
    dispatcher.add_handler(sat_in_usd_handler)
    dispatcher.add_handler(sat_in_chf_handler)
    dispatcher.add_handler(blockzeit_handler)
    dispatcher.add_handler(moskauzeit_handler)
    dispatcher.add_handler(episode_handler)
    dispatcher.add_handler(shoutout_handler)
    dispatcher.add_handler(glaskugel_handler)
    dispatcher.add_handler(soundboard_handler)
    dispatcher.add_handler(soundboard_callback_handler)

    job_queue = dispatcher.job_queue

    if config.FEATURE_ATH:
        job_queue.run_repeating(price_update_ath, 10)

    if config.USE_WEBHOOK:
        updater.start_webhook(
            listen='0.0.0.0',
            port=config.WEBHOOK_PORT,
            webhook_url=f'https://{config.WEBHOOK_URL}:{config.WEBHOOK_PORT}/{bot_token}',
            url_path=bot_token,
            cert='cert.pem',
            key='private.key'
        )
        updater.idle()
    else:
        updater.start_polling()
