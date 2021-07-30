from telegram import Update
import requests
from bs4 import BeautifulSoup
from telegram.chat import Chat
from telegram.ext import ConversationHandler, CallbackContext
from textwrap import dedent

import json
import time

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
    return dict["lightning_pay_request"], dict["tc_payment_id"]

def createQR(text: str, chatid: int):
    """
    Creates a QR Code with the given text and saves it as a png file in the current directory
    """

    img = qrcode.make(text)
    img.save(f"{chatid}.png")

def checkPayment(paymentID):
    timeout = time.time() + 60*10
    paid = 0

    VERIFYDATA = {
        'payment_id': paymentID
    }

    while True:
        if paid == 1:
            return('Vielen Dank, wir haben deine Zahlung erhalten!')
        elif time.time() > timeout:
            return('Es konnte kein Zahlungseingang festgestellt werden')
        else:
            try:
                r = requests.post('https://api.tallyco.in/v1/payment/verify/', data=VERIFYDATA).text
                dict = json.loads(r)
                if dict["payment_state"] == 'paid':
                    paid = 1
            except:
                logging.error(f'ERROR: Failed to verify payment status')
                return('Es gab ein Problem beim Verifizieren der Zahlung. Wenn du die Invoice bezahlt hast, sollte dein Shoutout zeitnah auf https://tallyco.in/s/zfxqtu/ zu sehen sein.')
        time.sleep(20)


def shoutout(update: Update, context: CallbackContext) -> int:
    """
    Starts the shoutout-conversation and asks the user about the donation amount.
    """

    chat = update.effective_chat
    if chat != None and chat.type == Chat.PRIVATE:
        update.message.reply_text(dedent('''
        Hi! Du möchtest also einen Shoutout bei Einundzwanzig kaufen? Toll!\n
        Bitte nenne zuerst die Menge an Satoshis die du spenden möchtest (Bspw: 21000). Beachte, dass lediglich Spenden
        größer als <b>21.000</b> Satoshis in der nächsten Newsepisode vorgelesen werden.\n
        Du kannst den Vorgang jederzeit mit /cancel abbrechen.
        '''), parse_mode='HTML')
        return SHOUTOUT_AMOUNT
    else:
        update.message.reply_text('Shoutouts können nur im privaten Chat mit dem Bot gesendet werden. Bitte beginne einen direkten Chat mit @einundzwanzigbot.')
        return ConversationHandler.END


def memo(update: Update, context: CallbackContext) -> int:
    """
    Stores the amount and asks for the donation-message (memo)
    """

    if context.user_data == None:
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
    if context.user_data == None:
        update.message.reply_text(text='Es ist ein Fehler aufgetreten, bitte versuche es später noch mal')
        logging.error('context.user_data is None')
        return ConversationHandler.END

    if update.effective_chat == None:
        update.message.reply_text(text='Es ist ein Fehler aufgetreten, bitte versuche es später noch mal')
        logging.error('update.effecitve_chat is None')
        return ConversationHandler.END

    context.user_data['memo'] = memo

    sat_amount: int = context.user_data['amount']

    if len(memo) > 140:
        update.message.reply_text(text=f'Der Shoutout darf nicht länger als 140 Zeichen sein. Aktuelle Länge: {len(memo)} Zeichen.')
        return SHOUTOUT_MEMO
    else:
        
        try:
            invoice = getInvoice(sat_amount, memo) 
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text= f'Fehler beim Erstellen der Invoice! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate invoice: {e}')
            return ConversationHandler.END
        
        try:
            createQR(invoice[0], update.effective_chat.id)
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text= f'Fehler beim Erstellen des QR-Codes! Bitte versuche es später nochmal!')
            logging.error(f'Error while trying to generate QR code: {e}')
            return ConversationHandler.END

        shoutoutMessage = dedent(f'''
        <b>Dein Shoutout</b>
        Betrag: {sat_amount} Satoshis
        Memo: {memo}

        Sobald die Invoice bezahlt wurde ist der Vorgang abgeschlossen.
        Deine Nachricht und deine sats sind dann bei uns angekommen.
        ''')

        context.bot.send_message(chat_id=update.effective_chat.id, text=shoutoutMessage, parse_mode='HTML')
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f'{update.effective_chat.id}.png', 'rb'), caption=str(invoice[0]).lower())
        
        try:
            os.remove(f'{update.effective_chat.id}.png')
        except:
            logging.error(f'ERROR: QR-code file {update.effective_chat.id}.png could not be deleted')
        
        context.bot.send_message(chat_id=update.effective_chat.id, text=checkPayment(invoice[1]), parse_mode='HTML')
        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Shoutout abgebrochen.')
    
    return ConversationHandler.END