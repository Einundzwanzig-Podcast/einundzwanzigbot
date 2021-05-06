import logging
from telegram.ext import Updater, CommandHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

import config

from taproot import taproot_calculate_signalling_statistics
from mempool import mempool_space_fees, blockzeit
from price import moskauzeit

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
    taproot_calculate_signalling_statistics(update, context)

def fee_command(update: Update, context: CallbackContext):
    """
    Get fees for next blocks from mempool.space
    """
    mempool_space_fees(update, context)

def blockzeit_command(update: Update, context: CallbackContext):
    """
    Get the current block time (block height)
    """
    blockzeit(update, context)

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

    updater = Updater(token=bot_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start_command)
    taproot_handler = CommandHandler('taproot', taproot_command)
    fee_handler = CommandHandler('fee', fee_command)
    blockzeit_handler = CommandHandler('blockzeit', blockzeit_command)
    moskauzeit_handler = CommandHandler('moskauzeit', moskauzeit_command)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(taproot_handler)
    dispatcher.add_handler(fee_handler)
    dispatcher.add_handler(blockzeit_handler)
    dispatcher.add_handler(moskauzeit_handler)

    if config.USE_WEBHOOK:
        updater.start_webhook(
            listen=config.WEBHOOK_URL,
            port=config.WEBHOOK_PORT,
            cert='cert.pem',
            key='private.key'
        )
    else:
        updater.start_polling()
