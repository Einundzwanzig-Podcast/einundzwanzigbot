import datetime
import pytz
import requests
import math
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from textwrap import dedent
import config


class MempoolSpaceFees:
    def __init__(self, one_block_fee: int, three_block_fee: int, six_block_fee: int) -> None:
        self.one_block_fee = one_block_fee
        self.three_block_fee = three_block_fee
        self.six_block_fee = six_block_fee


def mempool_space_fees(update: Update, context: CallbackContext):
    """
    Recommended fees from mempool space
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/fees/recommended', timeout=5)
        json = r.json()
    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    fees = MempoolSpaceFees(
        one_block_fee=json['fastestFee'],
        three_block_fee=json['halfHourFee'],
        six_block_fee=json['hourFee']
    )

    message = dedent(f"""
    <b>Gebühren</b>
    Ein Block (10 min): {fees.one_block_fee} sat/vbyte
    Drei Blöcke (30 min): {fees.three_block_fee} sat/vbyte
    Sechs Blöcke (60 min): {fees.six_block_fee} sat/vbyte
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def fee_emoji(fee: float) -> str:
    """
    Returns an emoji depending on the fee
    """
    if fee > 100:
        return '🟥'
    if fee > 30:
        return '🟧'
    if fee > 10:
        return '🟨'
    return '🟩'


def mempool_space_mempool_stats(update: Update, context: CallbackContext):
    """
    Mempool statistics from mempool space
    """

    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/mempool', timeout=5)
        mempool = r.json()
    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/fees/mempool-blocks', timeout=5)
        blocks = r.json()
    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    try:
        num_blocks = int(context.args[0])
    except Exception as e:
        num_blocks = 3

    if num_blocks <= 0:
        num_blocks = 1

    message = dedent(f"""
    <b>Mempool</b>
    Anzahl: {'{0:,.0f}'.format(mempool['count'])} tx
    Backlog: {mempool['vsize'] / 1_000_000:.1f} vMB
    """)

    for index, block in enumerate(blocks):
        fee_range = block['feeRange']

        try:
            min_fee = fee_range[0]
            max_fee = fee_range[-1]
        except Exception as e:
            min_fee = 1.0
            max_fee = 1.0

        if index <= num_blocks - 1:
            message += dedent(f"""
            <i>Block {index + 1} (In ~{(index + 1) * 10} min)</i>
            {fee_emoji(max_fee)} Max: {max_fee:.1f} sat/vbyte 
            {fee_emoji(min_fee)} Min: {min_fee:.1f} sat/vbyte
            """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def blockzeit(update: Update, context: CallbackContext):
    """
    Returns the current block time (block height)
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/blocks/tip/height', timeout=5)
        height = r.json()
    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    message = dedent(f"""
    <b>Aktuelle Blockzeit</b>
    {height}
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def halving(update: Update, context: CallbackContext):
    """
    Returns the time until the next halving
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/blocks/tip/height', timeout=5)
        current_block_height = r.json()
    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    blocks_till_next_halving = 210_000 - current_block_height % 210_000

    minutes_till_next_halving = 10 * blocks_till_next_halving
    time_till_next_halving = datetime.timedelta(minutes=minutes_till_next_halving)

    now = datetime.datetime.now(pytz.timezone("Europe/Berlin"))
    time_of_next_halving = now + time_till_next_halving

    next_halving_block_height = (math.floor(current_block_height / 210_000) + 1) * 210_000

    current_block_reward = 50 / 2 ** math.floor(current_block_height / 210_000)
    next_block_reward = current_block_reward / 2

    message = dedent(f"""
    <b>Halving</b>
    Nächstes Halving bei Block: <i>{next_halving_block_height}</i>
    Aktueller Block: <i>{current_block_height}</i>
    Blöcke bis zum nächsten Halving: <i>{blocks_till_next_halving}</i>
    
    Aktuelle Block Subsidy: <i>{current_block_reward:g} BTC</i>
    Nächste Block Subsidy: <i>{next_block_reward:g} BTC</i>
    
    Geschätztes Datum des nächsten Halvings: <i>{time_of_next_halving.strftime('%d.%m.%Y %H:%M CET')}</i>
    Geschätzte Zeit bis zum nächsten Halving: <i>{time_till_next_halving.days} Tage {time_till_next_halving.seconds / 60 / 60:.0f} Stunden</i>
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def difficulty(update: Update, context: CallbackContext):
    """
    Returns information about the next difficulty adjustment
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/difficulty-adjustment', timeout=5)
        difficulty_json = r.json()
        difficulty_progress_percent = round(difficulty_json['progressPercent'], 2)
        difficulty_difficulty_change = round(difficulty_json['difficultyChange'], 2)
        difficulty_previous_retarget = round(difficulty_json['previousRetarget'], 2)
        difficulty_remaining_blocks = int(difficulty_json['remainingBlocks'])
        difficulty_remaining_days = int(difficulty_remaining_blocks/144)
        difficulty_next_retarget_height = int(difficulty_json['nextRetargetHeight'])

    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    message = dedent(f"""
    <b>Nächste Schwierigkeitsanpassung</b>
    {difficulty_emoji(difficulty_difficulty_change)} Schätzung: <i>{difficulty_difficulty_change} %</i>
    {difficulty_emoji(difficulty_previous_retarget)} Vorherige Anpassung: <i>{difficulty_previous_retarget} %</i>

    Laufende Periode: <i>{difficulty_progress_percent} %</i>
    Verbleibende Blöcke: <i>{difficulty_remaining_blocks} (ca. {difficulty_remaining_days} Tage)</i>
    Anpassung bei Block: <i>{difficulty_next_retarget_height} </i>


    Zur aktuellen Hashrate siehe /hashrate.
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')


def difficulty_emoji(difficulty_change: float) -> str:
    """
    Returns an emoji depending on the difficulty change
    """
    if difficulty_change < 0:
        return '🟥'
    if difficulty_change > 0:
        return '🟩'


def hashrate(update: Update, context: CallbackContext):
    """
    Returns information about current hashrate
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/mining/hashrate/3d', timeout=5)

        hash_rate_average = r.json()['hashrates']
        hash_rate_average = sum([n['avgHashrate'] for n in hash_rate_average]) / 3
        hash_rate_average_ehs = int(hash_rate_average / (10**18))
        current_hashrate = int(r.json()['currentHashrate'])
        current_hashrate_ehs = int(current_hashrate / (10**18))

        difficulty_int = int(r.json()['currentDifficulty'])
        diff_T = round((difficulty_int / (10**12)), 2)

    except Exception as e:
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    message = dedent(f"""
    <b>Hashrate</b>
    Durchschnittliche Hashrate der letzten drei Tage:  <i>{hash_rate_average_ehs} EH/s</i>. 
    Aktuelle Hashrate: <i>{current_hashrate_ehs} EH/s</i>.
    Aktuelle Schwierigkeit: <i>{diff_T} T</i>.

    Zur Schwierigkeitsanpassung siehe /difficulty.
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')
