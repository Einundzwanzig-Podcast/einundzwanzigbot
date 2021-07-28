from telegram import Update
import requests
from bs4 import BeautifulSoup
from telegram.chat import Chat
from telegram.ext import ConversationHandler, CallbackContext
from textwrap import dedent

import json

from telegram.utils.helpers import effective_message_type
import config
import qrcode
import os

import logging

# Define podcast formats
urlAll = '/podcast/'
urlNews = '/podcast/news/'
urlLese = '/podcast/lesestunde/'
urlWeg = '/podcast/der-weg/'
urlInterviews = '/podcast/interviews/'

SHOUTOUT_AMOUNT, SHOUTOUT_MEMO = range(2)

def getEpisode(url: str) -> str:
    """
    Returns the link to the most recent episode or an error message, if
    the request fails
    """

    try:
        r = requests.get(config.EINUNDZWANZIG_URL + url, timeout=5)
        doc = BeautifulSoup(r.text, "html.parser")
        return f"{config.EINUNDZWANZIG_URL + doc.select('.plain')[0].get('href')}"
    except:
        return "Es kann aktuell keine Verbindung zum Server aufgebaut werden. Schau doch solange auf Spotify vorbei: https://open.spotify.com/show/10408JFbE1n8MexfrBv33r"

def episode(update: Update, context: CallbackContext):
    """
    Sends a link to the most recent podcast episode
    """

    try:
        if context.args != None:
            format = str(context.args[0]).lower()
        else:
            format = "alle"
    except: 
        format = "alle"
    
    if format == "news":
        message = getEpisode(urlNews)
    elif format == "lesestunde":
        message = getEpisode(urlLese)
    elif format == "alle":
        message = getEpisode(urlAll)
    elif format == "weg":
        message = getEpisode(urlWeg)
    elif format == "interview":
        message = getEpisode(urlInterviews)
    else:
        message = 'Das ist kein gültiges Podcast-Format! Bitte gibt eins der folgenden Formate an: Alle, Interviews, Lesestunde, News, Weg'

    if update.effective_chat != None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def getInvoice(amt: int, memo: str) -> str:
    """
    Returns a Lightning Invoice from the Tallycoin API
    """
    
    TALLYDATA = {
    'type': 'fundraiser',
    'id': 'zfxqtu',
    'satoshi_amount': '21',
    'payment_method': 'ln',
    'message' : ''
    }
    
    TALLYDATA['satoshi_amount'] = str(amt)
    TALLYDATA['message'] = memo
    response = requests.post('https://api.tallyco.in/v1/payment/request/', data=TALLYDATA).text
    dict = json.loads(response)
    return dict["lightning_pay_request"]

def createQR(text: str, chatid: str):
    """
    Creates a QR Code with the given text and saves it as a png file in the current directory
    """

    img = qrcode.make(text)
    img.save(chatid + '.png')


def shoutout(update: Update, context: CallbackContext) -> int:
    """
    Starts the shoutout-conversation and asks the user about the donation amount.
    """

    chat = update.effective_chat
    if chat != None and chat.type == Chat.PRIVATE:
        update.message.reply_text(dedent('''
        Hi! Du möchtest also einen Shout-Out bei Einundzwanzig kaufen? Toll! Du kannst den Vorgang jederzeit mit /cancel abbrechen\n\n
        Bitte nenne jetzt die Menge an Satoshis die du spenden möchtest (Bspw: "21000"). Beachte, dass lediglich Spenden
        größer als 21.000 Satoshis in der nächsten Newsepisode vorgelesen werden 
        '''))
        return SHOUTOUT_AMOUNT
    else:
        update.message.reply_text('Shoutouts können nur im privaten Chat mit dem Bot gesendet werden. Bitte beginne einen direkten Chat mit @einundzwanzigbot !')
        return ConversationHandler.END


def memo(update: Update, context: CallbackContext) -> int:
    """
    Stores the amount and asks for the donation-message (memo)
    """
    
    text = update.message.text
    context.user_data['amount'] = int(text)
    update.message.reply_text(dedent(f'''
    Alles klar! Du möchtest also {context.user_data["amount"]} Satoshis spenden.\n\n
    Bitte füge deiner Spende noch eine Nachricht (max. 140 Zeichen) hinzu. Spenden über 21.000 Satoshi werden in der nächsten Newsepisode vorgelesen!
    '''))
    return SHOUTOUT_MEMO


def invoice(update: Update, context: CallbackContext) -> int:
    """
    Stores the message and returns the lightning invoice + qr code.
    """
    memo = update.message.text
    context.user_data['memo'] = memo
    amount = context.user_data['amount']
    if len(memo) > 140:
        update.message.reply_text(text='Der Shoutout darf nicht länger als 140 Zeichen sein. Bitte beginne von vorne')
        return ConversationHandler.END
    else:
        
        try:
            invoice = getInvoice(amount, memo)     
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text= f'Fehler beim Erstellen der Invoice! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate invoice: {e}')
            return
        
        try:
            createQR(invoice, update.effective_chat.id)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text= f'Fehler beim Erstellen des QR-Codes! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate QR code: {e}')
            return

        shoutoutMessage = dedent(f'''
        <b>Dein Shoutout</b>
        Betrag: {amount} Satoshis
        Memo: {memo}
        ''')

        context.bot.send_message(chat_id=update.effective_chat.id, text=shoutoutMessage)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f'{update.effective_chat.id}.png', 'rb'), caption=str(invoice).lower())
        
        try:
            os.remove(f'{update.effective_chat.id}.png')
        except:
            logging.error(f'ERROR: QR-code file {update.effective_chat.id}.png could not be deleted')
        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Shoutout Abgrebrochen! Bis zum nächsten mal!')
    
    return ConversationHandler.END