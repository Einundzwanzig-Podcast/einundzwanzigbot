from telegram.ext import Updater
import requests
from bs4 import BeautifulSoup
from telegram.ext import CommandHandler
import config

# Define podcast formats
urlAll = '/podcast/'
urlNews = '/podcast/news/'
urlLese = '/podcast/lesestunde/'
urlWeg = '/podcast/der-weg/'
urlInterviews = '/podcast/interviews/'

def getEpisode(url):
    try:
        r = requests.get(url, timeout=5)
        doc = BeautifulSoup(r.text, "html.parser")
        return({config.EINUNDZWANZIG_URL} +(doc.select(".plain")[0].get("href")))
    except:
        return('Es kann aktuell keine Verbindung zum Server aufgebaut werden. Schau doch solange auf Spotify vorbei: https://open.spotify.com/show/10408JFbE1n8MexfrBv33r')

def episode(update, context):
    try:
        format = str(context.args[0]).lower()
    except: format = "alle"
    
    if format == "news":
        message = getEpisode({config.EINUNDZWANZIG_URL} + urlNews)
    elif format == "lesestunde":
        message = getEpisode({config.EINUNDZWANZIG_URL} + urlLese)
    elif format == "alle":
        message = getEpisode({config.EINUNDZWANZIG_URL} + urlAll)
    elif format == "weg":
        message = getEpisode({config.EINUNDZWANZIG_URL} + urlWeg)
    elif format == "interview":
        message = getEpisode({config.EINUNDZWANZIG_URL} + urlInterviews)
    else:
        message = 'Das ist kein gültiges Podcast-Format! Bitte gibt eins der folgenden Formate an: Alle, Interviews, Lesestunde, News, Weg'
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)