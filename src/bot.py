import logging
from telegram.ext import Updater, CommandHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.dispatcher import run_async
from telegram.update import Update

import config

from database import setup_database
from taproot import taproot_handle_command
from mempool import blockzeit, mempool_space_mempool_stats, mempool_space_fees
from price import moskauzeit, preis, price_update_ath

def start_command(update: Update, context: CallbackContext):
    """
    Sends a welcome message to the user
    Should be customized in the future
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi, ich bin der Einundzwanzig Community Bot!")

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
    Get the current price in USD and EUR
    """
    preis(update, context)

def moskauzeit_command(update: Update, context: CallbackContext):
    """
    Get the current moscow time (sat/USD and sat/EUR)
    """
    moskauzeit(update, context)

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
    blockzeit_handler = CommandHandler('blockzeit', blockzeit_command, run_async=True)
    moskauzeit_handler = CommandHandler('moskauzeit', moskauzeit_command, run_async=True)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(taproot_handler)
    dispatcher.add_handler(fee_handler)
    dispatcher.add_handler(mempool_handler)
    dispatcher.add_handler(preis_handler)
    dispatcher.add_handler(blockzeit_handler)
    dispatcher.add_handler(moskauzeit_handler)

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
