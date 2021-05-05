import requests
from typing import List, Any, Optional
from telegram.ext.callbackcontext import CallbackContext
import config

def fetch_latest_blocks() -> List[Any]:
    """
    Get the latest Taproot block statistics using the API
    from https://taproot.watch
    """
    r = requests.get('https://taproot.watch/blocks')
    return r.json()

def new_miner_signalling(context: CallbackContext):
    """
    Sends a message to chat if a new miner starts signalling for Taproot
    """

    blocks = fetch_latest_blocks()

    new_signalling_miners: List[str] = []

    for block in blocks:
        if 'signals' in block and block['signals'] == True:
            if block['miner'] not in config.signalling_miners:
                new_signalling_miners.append(block['miner'])

    amount = len(new_signalling_miners)
    
    if amount == 1:
        context.bot.send_message(chat_id=config.einundzwanzig_chat_id, text=f"<b>Ein neuer Miner signalisiert Taproot!</b>\n{new_signalling_miners[0]} ✅", parse_mode='HTML')
    
    if amount > 1:
        context.bot.send_message(chat_id=config.einundzwanzig_chat_id, text=f"<b>Neue Miner signalisieren Taproot!</b>\n{', '.join([str(x) + ' ✅' for x in new_signalling_miners])}", parse_mode='HTML')

def taproot_signalling_blocks(context: Optional[CallbackContext]):
    """
    Calculate how many blocks are signalling
    """

    blocks = fetch_latest_blocks()

    config.blocks_mined = 0
    config.signal_true = 0
    config.signal_false = 0

    config.miner_stats = {}

    for block in blocks:

        if 'signals' in block:

            if 'miner' not in block:
                block['miner'] = 'Unbekannt'

            # Add miner to stats if not already added
            if not block['miner'] in config.miner_stats.keys():
                config.miner_stats[block['miner']] = { 
                    'signal_true': 0,
                    'signal_false': 0,
                    'blocks_mined': 0
                }

            config.blocks_mined += 1
            config.miner_stats[block['miner']]['blocks_mined'] += 1

            if block['signals'] == True:
                config.signal_true += 1
                config.miner_stats[block['miner']]['signal_true'] += 1

                if block['miner'] not in config.signalling_miners:
                    config.signalling_miners.append(block['miner'])
            else:
                config.signal_false += 1
                config.miner_stats[block['miner']]['signal_false'] += 1
