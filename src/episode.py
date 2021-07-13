from telegram.ext import Updater
import requests
from bs4 import BeautifulSoup
from telegram.ext import CommandHandler

# Define podcast formats
urlHome = 'https://einundzwanzig.space'
urlNews = 'https://einundzwanzig.space/podcast/news/'
urlLese = 'https://einundzwanzig.space/podcast/lesestunde/'
urlWeg = 'https://einundzwanzig.space/podcast/der-weg/'
urlAll = 'https://einundzwanzig.space/podcast/'
urlInterviews = 'https://einundzwanzig.space/podcast/interviews/'

def getEpisode(url):
    r = requests.get(url)
    doc = BeautifulSoup(r.text, "html.parser")
    return(urlHome +(doc.select(".plain")[0].get("href")))

def episode(update, context):
    try:
        format = str(context.args[0]).lower()
    except: format = "alle"
    
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

episode_handler = CommandHandler('Episode', episode)
dispatcher.add_handler(episode_handler)