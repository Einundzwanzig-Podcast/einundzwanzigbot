from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import requests
from bs4 import BeautifulSoup
from telegram.chat import Chat
from telegram.ext import ConversationHandler, CallbackContext
from textwrap import dedent

import json

import config
import qrcode
import os
import time

import logging

# Define podcast formats
urlAll = '/podcast/'
urlNews = '/podcast/news/'
urlLese = '/podcast/lesestunde/'
urlWeg = '/podcast/der-weg/'
urlInterviews = '/podcast/interviews/'

SHOUTOUT_AMOUNT, SHOUTOUT_MEMO = range(2)


def get_episode(url: str) -> str:
    """
    Returns the link to the most recent episode or an error message, if
    the request fails
    """

    try:
        r = requests.get(config.EINUNDZWANZIG_URL + url, timeout=5)
        doc = BeautifulSoup(r.text, "html.parser")
        return f"{config.EINUNDZWANZIG_URL + doc.select('.plain')[0].get('href')}"
    except:
        return "Es kann aktuell keine Verbindung zum Server aufgebaut werden. Schau doch solange auf Spotify vorbei: " \
               "https://open.spotify.com/show/10408JFbE1n8MexfrBv33r "


def episode(update: Update, context: CallbackContext):
    """
    Sends a link to the most recent podcast episode
    """

    try:
        if context.args is not None:
            episode_format = str(context.args[0]).lower()
        else:
            episode_format = "alle"
    except:
        episode_format = "alle"

    if episode_format == "news":
        message = get_episode(urlNews)
    elif episode_format == "lesestunde":
        message = get_episode(urlLese)
    elif episode_format == "alle":
        message = get_episode(urlAll)
    elif episode_format == "weg":
        message = get_episode(urlWeg)
    elif episode_format == "interview":
        message = get_episode(urlInterviews)
    else:
        message = 'Das ist kein gültiges Podcast-Format! Bitte gibt eins der folgenden Formate an: Alle, Interviews, ' \
                  'Lesestunde, News, Weg '

    if update.effective_chat is not None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def get_invoice(amt: int, memo: str) -> str:
    """
    Returns a Lightning Invoice from the Tallycoin API
    """

    tallydata = {'type': 'fundraiser', 'id': 'zfxqtu', 'satoshi_amount': str(amt), 'payment_method': 'ln',
                 'message': memo}

    response = requests.post('https://api.tallyco.in/v1/payment/request/', data=tallydata).text
    dict = json.loads(response)
    return dict["lightning_pay_request"]


def create_qr(text: str, chat_id: int):
    """
    Creates a QR Code with the given text and saves it as a png file in the current directory
    """

    img = qrcode.make(text)
    img.save(f"{chat_id}.png")


def shoutout(update: Update, context: CallbackContext) -> int:
    """
    Starts the shoutout conversation and asks the user about the donation amount.
    """

    chat = update.effective_chat
    if chat is not None and chat.type == Chat.PRIVATE:
        update.message.reply_text(dedent('''
        Hi! Du möchtest also einen Shoutout bei Einundzwanzig kaufen? Toll!\n
        Bitte nenne zuerst die Menge an Satoshis die du spenden möchtest (Bspw: 21000). Beachte, dass lediglich Spenden
        größer als <b>21.000</b> Satoshis in der nächsten Newsepisode vorgelesen werden.\n
        Du kannst den Vorgang jederzeit mit /cancel abbrechen.
        '''), parse_mode='HTML')
        return SHOUTOUT_AMOUNT
    else:
        update.message.reply_text(
            f'Shoutouts können nur im privaten Chat mit dem Bot gesendet werden. Bitte beginne einen direkten Chat mit '
            f'{context.bot.name}.')
        return ConversationHandler.END


def memo(update: Update, context: CallbackContext) -> int:
    """
    Stores the amount and asks for the donation-message (memo)
    """

    if context.user_data is None:
        update.message.reply_text(text='Es ist ein Fehler aufgetreten, bitte versuche es später noch mal')
        logging.error('context.user_data is None')
        return ConversationHandler.END

    try:
        sat_amount = int(update.message.text)

        if sat_amount <= 0:
            update.message.reply_text(text='Der Betrag darf nicht kleiner oder gleich 0 sein!')
            return SHOUTOUT_AMOUNT

        context.user_data['amount'] = sat_amount
    except:
        update.message.reply_text(text='Bitte gib eine korrekte Anzahl von sats ein!')
        return SHOUTOUT_AMOUNT

    update.message.reply_text(dedent(f'''
    Alles klar! Du möchtest also {sat_amount} Satoshis spenden.\n
    Bitte füge deiner Spende noch eine Nachricht (max. 140 Zeichen) hinzu.
    '''))

    return SHOUTOUT_MEMO


def invoice(update: Update, context: CallbackContext) -> int:
    """
    Stores the message and returns the lightning invoice + qr code.
    """
    memo = update.message.text

    # If we don't have user data we need to abort
    if context.user_data is None:
        update.message.reply_text(text='Es ist ein Fehler aufgetreten, bitte versuche es später noch mal')
        logging.error('context.user_data is None')
        return ConversationHandler.END

    if update.effective_chat is None:
        update.message.reply_text(text='Es ist ein Fehler aufgetreten, bitte versuche es später noch mal')
        logging.error('update.effecitve_chat is None')
        return ConversationHandler.END

    context.user_data['memo'] = memo

    sat_amount: int = context.user_data['amount']

    if len(memo) > 140:
        update.message.reply_text(
            text=f'Der Shoutout darf nicht länger als 140 Zeichen sein. Aktuelle Länge: {len(memo)} Zeichen.')
        return SHOUTOUT_MEMO
    else:

        try:
            invoice = get_invoice(sat_amount, memo)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Fehler beim Erstellen der Invoice! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate invoice: {e}')
            return ConversationHandler.END

        try:
            create_qr(invoice, update.effective_chat.id)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Fehler beim Erstellen des QR-Codes! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate QR code: {e}')
            return ConversationHandler.END

        shoutout_message = dedent(f'''
        <b>Dein Shoutout</b>
        Betrag: {sat_amount} Satoshis
        Memo: {memo}

        Sobald die Invoice bezahlt wurde ist der Vorgang abgeschlossen.
        Du kannst den Status deiner Zahlung hier überprüfen: https://tallyco.in/s/zfxqtu/
        Bitte beachte, dass es etwas dauern kann, bevor dein Shoutout auf Tallyco.in angezeigt wird.
        Invoice wird erstellt, bitte warten...
        ''')

        context.bot.send_message(chat_id=update.effective_chat.id, text=shoutout_message, parse_mode='HTML',
                                 disable_web_page_preview=True)
        time.sleep(5)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f'{update.effective_chat.id}.png', 'rb'),
                               caption=str(invoice).lower())

        try:
            os.remove(f'{update.effective_chat.id}.png')
        except:
            logging.error(f'ERROR: QR-code file {update.effective_chat.id}.png could not be deleted')

        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Shoutout abgebrochen.')

    return ConversationHandler.END


def soundboard(update: Update, context: CallbackContext):
    """Get the soundboard markup from the Einundzwanzig website"""
    chat = update.effective_chat

    if chat is not None and chat.type != Chat.PRIVATE:
        update.message.reply_text(
            f'Das Soundboard kann nur im privaten Chat mit dem Bot gesendet werden. Bitte beginne einen direkten Chat '
            f'mit {context.bot.name}.')
        return

    try:
        sounds_request = requests.get(f'{config.EINUNDZWANZIG_URL}/sounds.json', timeout=5)
    except:
        update.message.reply_text('Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    sounds_dict = json.loads(sounds_request.text)

    keyboard = []

    for group in sounds_dict:
        # Set the callback data to "group_" and then the group name
        keyboard.append([InlineKeyboardButton(group['title'], callback_data=f"group_{group['title']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # We need a reference to the sound dict for use in the callback query
    context.user_data['sounds_dict'] = sounds_dict

    update.message.reply_text('Bitte wähle eine Kategorie', reply_markup=reply_markup)


def soundboard_button(update: Update, context: CallbackContext):
    """Handles the callback query"""

    query = update.callback_query
    query.answer()

    sounds_dict = context.user_data['sounds_dict']

    if query.data == 'back_button':
        # Handle pressing the back button on the first level
        keyboard = []

        for group in sounds_dict:
            keyboard.append([InlineKeyboardButton(group['title'], callback_data=f"group_{group['title']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text('Bitte wähle eine Kategorie', reply_markup=reply_markup)

    elif query.data.startswith('group_'):
        # Handles pressing a sound group
        keyboard = []
        sounds = []

        # Remove the "group_" from the message
        group_title = query.data[6:]
        group_index = 0

        for index, group in enumerate(sounds_dict):
            if group['title'] == group_title:
                sounds = group['sounds']
                group_index = index
                break

        for index, sound in enumerate(sounds):
            # We set the level where the sound sits in the json hierarchy as the callback data
            keyboard.append([InlineKeyboardButton(sound['title'], callback_data=f'{str(group_index)}_{str(index)}')])

        keyboard.append([InlineKeyboardButton('🔙', callback_data='back_button')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.edit_message_text(text=f'Auswahl: {group_title}', reply_markup=reply_markup)

    else:
        # Handles pressing one of the sounds
        hierarchy = query.data.split('_')
        group_index = int(hierarchy[0])
        sound_index = int(hierarchy[1])

        sound_url = context.user_data['sounds_dict'][group_index]['sounds'][sound_index]['url']

        query.delete_message()
        context.bot.send_audio(chat_id=update.effective_message.chat_id, audio=str(sound_url))

def show_meetups(update: Update, context: CallbackContext):

    try:
        meetup_request = requests.get(f'{config.EINUNDZWANZIG_URL}/meetups.json', timeout=5)
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return
  
    meetup_dict = json.loads(meetup_request.text)

   # stores the message
    meetup_string = ''

    # loop through all meetups and add them to the message
    meetups = meetup_dict
    for meetup in meetups:

        meetup_string = meetup_string + (str(meetup) + '\n\n')
        
    
    meetup_string = meetup_string.replace('{', '')
    meetup_string = meetup_string.replace('}', '')
    meetup_string = meetup_string.replace("'", '')
    meetup_string = meetup_string.replace('"', '')
    
    context.bot.send_message(chat_id=update.message.chat_id, text=meetup_string)
