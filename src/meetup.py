# this class is about to collect all meetups from einundzwanzig.space/meetups.json
# and returns a (Telegram-)message with all meetups (command: /meetup)

import config

from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update

import requests

class Meetup:

    def __init__(self, name: str, region: str, url: str) -> None:
        self.name = name
        self.region = region
        self.url = url


def show_meetups(update: Update, context: CallbackContext):


    # get json file from website
    url = requests.get(f'{config.EINUNDZWANZIG_URL}/meetups.json', timeout=5)
    json_string = url.text

    # save json file as string
    json_string = str(json_string)

    # count meetups
    # use "{" to count, for each "{" there is one meetup
    count = 0

    for i in json_string:
        if i == '{':
            
            count = count + 1

    # remove all special chars from json string
    json_string = json_string.replace('{', '')
    json_string = json_string.replace('}', '')
    json_string = json_string.replace('[', '')
    json_string = json_string.replace(']', '')
    json_string = json_string.replace('"', '')
    json_string = json_string.replace("'", '')

    # create lists to store all names, regions and url of all meetups
    meetup_name_list : str = []
    meetup_region_list : str = []
    meetup_url_list : str = []

    # get a new String Array to access meetup names, regions and urls via index
    json_string = json_string.splitlines()
    
    # lines/index of the first meetup
    name_index = 2
    region_index = 3
    url_index = 4

    # stores the message
    meetup_string = ''

    # loop through all meetups and add them to the message
    for x in range(count):

        # add values to lists and remove leading spaces,
        # remove last char for region and name (last char is always ",")
        meetup_name_list.append(json_string[name_index].lstrip()[:-1])
        name_index = name_index + 5
        meetup_string = meetup_string + meetup_name_list[x] + '\n'

        meetup_region_list.append(json_string[region_index].lstrip()[:-1])
        region_index = region_index + 5
        meetup_string = meetup_string + meetup_region_list[x] + '\n'

        meetup_url_list.append(json_string[url_index].lstrip())
        url_index = url_index + 5
        meetup_string = meetup_string + meetup_url_list[x] + '\n' + '\n'
        
            

    context.bot.send_message(chat_id=update.message.chat_id, text=meetup_string)


        


