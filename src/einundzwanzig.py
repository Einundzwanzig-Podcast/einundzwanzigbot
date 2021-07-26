from telegram import Update
import requests
from bs4 import BeautifulSoup
from telegram.ext import ConversationHandler, CallbackContext

import json
import config
import qrcode
import os


# Define podcast formats
urlAll = '/podcast/'
urlNews = '/podcast/news/'
urlLese = '/podcast/lesestunde/'
urlWeg = '/podcast/der-weg/'
urlInterviews = '/podcast/interviews/'

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
        format = str(context.args[0]).lower()
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

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def getInvoice(amt, shoutout):
    TALLYDATA = {
    'type': 'fundraiser',
    'id': 'zfxqtu',
    'satoshi_amount': '21',
    'payment_method': 'ln',
    'message' : ''
    }
    
    TALLYDATA['satoshi_amount'] = str(amt)
    TALLYDATA['message'] = shoutout[0:139]
    response = requests.post('https://api.tallyco.in/v1/payment/request/', data=TALLYDATA).text
    dict = json.loads(response)
    return dict.get("lightning_pay_request")

def createQR(text, chatid):
    img = qrcode.make(text)
    img.save(str(chatid) + '.png')

SHOUTOUT_AMOUNT, SHOUTOUT_MEMO = range(2)


def shoutout(update: Update, context: CallbackContext) -> int:
    """Starts the shoutout-conversation and asks the user about the donation amount."""
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        update.message.reply_text(
        'Hi! Du möchtest also einen Shout-Out bei Einundzwanzig kaufen? (Du kannst den Vorgang jederzeit mit /cancel abbrechen)\n\n'
        'Falls ja, bitte nenne jetzt die Menge an Satoshis die du spenden möchtest als Zahl (Bspw: "21000").',)
        return SHOUTOUT_AMOUNT
    else:
        update.message.reply_text('Shoutouts können nur im privaten Chat mit dem Bot erstellt werden')
        return ConversationHandler.END


def memo(update: Update, context: CallbackContext) -> int:
    """Stores the amount and asks for the doantion-message"""
    
    text = update.message.text
    context.user_data['amount'] = int(text)
    update.message.reply_text(
        f'''Alles klar! Du möchtest also {context.user_data["amount"]} Satoshis spenden.\n\n
Bitte füge deiner Spende noch eine Nachricht (max. 140 Zeichen) hinzu. Spenden über 21.000 Satoshi werden in der nächsten Newsepisode vorgelesen!''')
    return SHOUTOUT_MEMO


def invoice(update: Update, context: CallbackContext) -> int:
    """Stores the message and returns the lightning invoice + qr code."""
    message = update.message.text
    context.user_data['message'] = message
    amount = context.user_data['amount']

    invoice = getInvoice(amount, message)
    createQR(invoice, update.effective_chat.id)
    context.bot.send_message(chat_id=update.effective_chat.id, text= f'Hier ist deine Shoutout-Invoice über {amount} sats:')
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(str(update.effective_chat.id) + '.png', 'rb'), caption=str(invoice))
    try:
        os.remove(str(update.effective_chat.id) + '.png')
    except:
        print('ERROR: QR-Datei konnte nicht gelöscht werden')
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    update.message.reply_text('Shoutout Abgrebrochen! Bis zum nächsten mal!')
    
    return ConversationHandler.END