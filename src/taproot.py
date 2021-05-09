import requests
import logging
from typing import List, Any, Optional, Dict
from telegram.ext.callbackcontext import CallbackContext
from textwrap import dedent
from telegram.update import Update
import config

class TaprootStats:
    """
    Wrapper class for taproot stats
    """
    def __init__(self) -> None:
        # List of all signalling miners
        self.signalling_miners: List[str] = []

        self.blocks_mined = 0
        self.signal_true = 0
        self.signal_false = 0

        self.miner_stats: Dict = {}

def fetch_latest_blocks() -> List[Any]:
    """
    Get the latest Taproot block statistics using the API
    from https://taproot.watch
    """
    r = requests.get(f'{config.TAPROOT_WATCH_URL}/blocks', timeout=5)
    return r.json()

def new_miner_signalling(context: CallbackContext, taprootStats: TaprootStats):
    """
    Sends a message to chat if a new miner starts signalling for Taproot
    """
    try:
        blocks = fetch_latest_blocks()
    except:
        return

    new_signalling_miners: List[str] = []

    for block in blocks:
        if 'signals' in block and block['signals'] == True:
            if block['miner'] not in taprootStats.signalling_miners:
                new_signalling_miners.append(block['miner'])

    amount = len(new_signalling_miners)
    
    if amount == 1:
        context.bot.send_message(chat_id=config.EINUNDZWANZIG_CHAT_ID, text=f"<b>Ein neuer Miner signalisiert Taproot!</b>\n{new_signalling_miners[0]} ✅", parse_mode='HTML')
    
    if amount > 1:
        context.bot.send_message(chat_id=config.EINUNDZWANZIG_CHAT_ID, text=f"<b>Neue Miner signalisieren Taproot!</b>\n{', '.join([str(x) + ' ✅' for x in new_signalling_miners])}", parse_mode='HTML')

def taproot_signalling_blocks() -> TaprootStats:
    """
    Calculate how many blocks are signalling
    """

    blocks = fetch_latest_blocks()

    taprootStats = TaprootStats()

    for block in blocks:

        if 'signals' in block:

            if 'miner' not in block:
                block['miner'] = 'Unbekannt'

            # Add miner to stats if not already added
            if not block['miner'] in taprootStats.miner_stats.keys():
                taprootStats.miner_stats[block['miner']] = { 
                    'signal_true': 0,
                    'signal_false': 0,
                    'blocks_mined': 0
                }

            taprootStats.blocks_mined += 1
            taprootStats.miner_stats[block['miner']]['blocks_mined'] += 1

            if block['signals'] == True:
                taprootStats.signal_true += 1
                taprootStats.miner_stats[block['miner']]['signal_true'] += 1

                if block['miner'] not in taprootStats.signalling_miners:
                    taprootStats.signalling_miners.append(block['miner'])
            else:
                taprootStats.signal_false += 1
                taprootStats.miner_stats[block['miner']]['signal_false'] += 1

    return taprootStats

def sort_by_part_of_hashrate(item, taprootStats: TaprootStats):
    """
    Sorts the mined blocks by the part of the hashrate
    that the individual miners contributed (ascending)
    """

    if taprootStats.blocks_mined == 0:
        return 0
    
    miner_signal_true = item[1]['signal_true']
    miner_signal_false = item[1]['signal_false']
    miner_signal_total = miner_signal_true + miner_signal_false

    part_of_hashrate = miner_signal_total / taprootStats.blocks_mined

    return part_of_hashrate

def taproot_calculate_signalling_statistics(update: Update, context: CallbackContext):
    """
    Calculates Taproot Activation Statistics
    """

    try:
        taprootStats = taproot_signalling_blocks()
    except:
        update.message.reply_text(text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return
    
    try:

        signalling_percentage = 0.0

        # Prevent division by 0
        if taprootStats.signal_true != 0:
            signalling_percentage = taprootStats.signal_true / (taprootStats.signal_true + taprootStats.signal_false)

        current_cycle_activation_possible = False if taprootStats.signal_false > 201 else True

        activation_message = None

        if not current_cycle_activation_possible:
            activation_message = "Fehlgeschlagen 😭"
        else: 
            if taprootStats.signal_true >= 1815:
                activation_message = "Erfolgreich 🎉🎉🎉"
            else:
                activation_message = "Möglich 🙏"

        message = dedent(f"""
        <b>Taproot Aktivierung</b>
        Geschürfte Blöcke: {taprootStats.blocks_mined} / 2016
        Benötigt: 1815 / 2016 (90%)
        Signalisieren dafür: {taprootStats.signal_true} ({signalling_percentage * 100:.1f}%)
        Signalisieren nicht: {taprootStats.signal_false} ({(1 - signalling_percentage) * 100:.1f}%)

        <b>Aktueller Zyklus</b>
        Aktivierung: {activation_message}

        <b>Mining Pools</b>        
        """)

        total_signalling_hashrate = 0.0

        # Sort by part of hash rate
        miners_sorted = dict(sorted(taprootStats.miner_stats.items(), key=lambda item: sort_by_part_of_hashrate(item, taprootStats), reverse=True))

        for miner in miners_sorted.keys():

            miner_signal_true = taprootStats.miner_stats[miner]['signal_true']
            miner_signal_false = taprootStats.miner_stats[miner]['signal_false']
            miner_signal_total = miner_signal_true + miner_signal_false

            # Prevent division by 0 if no blocks have been mined yet in the cycle
            if taprootStats.blocks_mined == 0:
                part_of_hashrate = 0
            else:
                part_of_hashrate = miner_signal_total / taprootStats.blocks_mined
            
            if miner_signal_true > 0:
                total_signalling_hashrate += part_of_hashrate
                message += dedent(f"{miner} ✅ ({miner_signal_true} / {miner_signal_total}) Hash: {part_of_hashrate * 100:.1f}%\n")

        message += dedent(f"\n<b>Summe Hash: {total_signalling_hashrate * 100:.1f}%</b>")

        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML', disable_web_page_preview=True)

    except Exception as e:
        logging.log(logging.ERROR, e)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Es ist ein Fehler aufgetreten")
