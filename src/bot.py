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

def sort_by_part_of_hashrate(item):
    """
    Sorts the mined blocks by the part of the hashrate
    that the individual miners contributed (ascending)
    """

    if config.blocks_mined == 0:
        return 0
    
    miner_signal_true = item[1]['signal_true']
    miner_signal_false = item[1]['signal_false']
    miner_signal_total = miner_signal_true + miner_signal_false

    part_of_hashrate = miner_signal_total / config.blocks_mined

    return part_of_hashrate

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
            activation_message = "Fehlgeschlagen 😭"
        else: 
            if config.signal_true >= 1815:
                activation_message = "Erfolgreich 🎉🎉🎉"
            else:
                activation_message = "Möglich 🙏"

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

        total_signalling_hashrate = 0.0

        # Sort by part of hash rate
        miners_sorted = dict(sorted(config.miner_stats.items(), key=lambda item: sort_by_part_of_hashrate(item), reverse=True))

        for miner in miners_sorted.keys():

            miner_signal_true = config.miner_stats[miner]['signal_true']
            miner_signal_false = config.miner_stats[miner]['signal_false']
            miner_signal_total = miner_signal_true + miner_signal_false

            # Prevent division by 0 if no blocks have been mined yet in the cycle
            if config.blocks_mined == 0:
                part_of_hashrate = 0
            else:
                part_of_hashrate = miner_signal_total / config.blocks_mined
            
            if miner_signal_true > 0:
                total_signalling_hashrate += part_of_hashrate
                message += dedent(f"{miner} ✅ ({miner_signal_true} / {miner_signal_total}) Hash: {part_of_hashrate * 100:.1f}%\n")

        message += dedent(f"\n<b>Summe Hash: {total_signalling_hashrate * 100:.1f}%</b>")

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML', disable_web_page_preview=True)

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
