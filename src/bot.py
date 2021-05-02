import logging
from telegram.ext import Updater, CommandHandler, JobQueue
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from textwrap import dedent
from taproot import taproot_signalling_blocks
import config

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi, ich bin der Einundzwanzig Community Bot!")

def taproot(update: Update, context: CallbackContext):
    try:

        signalling_percentage = 0.0

        if config.signal_true != 0:
            signalling_percentage = config.signal_true / (config.signal_true + config.signal_false)

        message = dedent(f"""
        <b>Taproot Aktivierung</b>
        Geschürfte Blöcke: {config.blocks_mined} / 2016
        Benötigt: 1815 / 2016 (90%)
        Signalisieren dafür: {config.signal_true} ({signalling_percentage * 100:.1f}%)
        Signalisieren nicht: {config.signal_false} ({(1 - signalling_percentage) * 100:.1f}%)

        <b>Mining Pools</b>        
        """)

        for miner in config.signalling_miners:
            message += dedent(f"{miner} ✅\n")

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')

    except Exception as e:
        logging.log(logging.ERROR, e)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Es ist ein Fehler aufgetreten")

def run(bot_token: str):

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    updater = Updater(token=bot_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    taproot_handler = CommandHandler('taproot', taproot)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(taproot_handler)

    j = updater.job_queue
    j.run_repeating(taproot_signalling_blocks, interval=60, first=0.1)

    updater.start_polling()
