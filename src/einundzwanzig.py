from telegram import Update
import requests
from bs4 import BeautifulSoup
from telegram.ext.callbackcontext import CallbackContext
import json
import config

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
    config.TALLYDATA['satoshi_amount'] = str(amt)
    config.TALLYDATA['message'] = shoutout[0:139]
    response = requests.post('https://api.tallyco.in/v1/payment/request/', data=config.TALLYDATA).text
    dict = json.loads(response)
    return dict.get("lightning_pay_request")

def shoutout(update: Update, context: CallbackContext):
    """
    Returns a TallyCoin LN invoice for a specific amount thats includes a memo
    """
    try:
        value = int(context.args[0])
        try:
            shoutout = ' '.join(context.args[1:])
        except:
            shoutout = f'Community-Bot Shoutout'
        invoice = getInvoice(value, shoutout)
        context.bot.send_message(chat_id=update.effective_chat.id, text= f'Hier ist deine Shoutout-Invoice über {value} sats:')
        context.bot.send_message(chat_id=update.effective_chat.id, text= str(invoice))
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text= f'Bitte gib einen gültigen Betrag ein')