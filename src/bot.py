import logging
from telegram.ext import Updater, CommandHandler, JobQueue
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from textwrap import dedent
from taproot import taproot_signalling_blocks
import config

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
    try:

        signalling_percentage = 0.0

        # Prevent division by 0
        if config.signal_true != 0:
            signalling_percentage = config.signal_true / (config.signal_true + config.signal_false)

        current_cycle_activation_possible = False if config.signal_false > 201 else True

        activation_message = None

        if not current_cycle_activation_possible:
            activation_message = "Fehlgeschlagen 😭😭😭"
        else: 
            if config.signal_true >= 1815:
                activation_message = "Erfolgreich 🎉🎉🎉"
            else:
                activation_message = "Möglich 🙏🙏🙏"

        message = dedent(f"""
        <b>Taproot Aktivierung</b>
        Geschürfte Blöcke: {config.blocks_mined} / 2016
        Benötigt: 1815 / 2016 (90%)
        Signalisieren dafür: {config.signal_true} ({signalling_percentage * 100:.1f}%)
        Signalisieren nicht: {config.signal_false} ({(1 - signalling_percentage) * 100:.1f}%)

        <b>Aktueller Zyklus</b>
        Aktivierung: {activation_message}

        <b>Mining Pools</b>        
        """)

        for miner in config.signalling_miners:
            message += dedent(f"{miner} ✅\n")

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')

    except Exception as e:
        logging.log(logging.ERROR, e)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Es ist ein Fehler aufgetreten")

def run(bot_token: str):
    """
    Starts the bot
    """

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    updater = Updater(token=bot_token)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start_command)
    taproot_handler = CommandHandler('taproot', taproot_command)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(taproot_handler)

    j = updater.job_queue

    # Fetch statistics every 60 seconds
    j.run_repeating(taproot_signalling_blocks, interval=60)

    # Run once at startup
    taproot_signalling_blocks(None)

    updater.start_polling()
