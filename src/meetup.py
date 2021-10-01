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
    url = requests.get(f'{config.MEMPOOL_SPACE_URL}/meetups.json', timeout=5)
    json_string = url.json

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

    # get meetup names, regions and urls
    # need to use other strings, because String gets splited later
    n1 = 'name: '
    n2 = ', region: '

    r1 = 'region: '
    r2 = ', url: '

    url1 = 'url: '
    url2 = ', name: '

    # create String Arrays to save meetups
    name_list : str = []
    region_list : str = []
    url_list : str = []

    # store values for lists temporary in result
    result = ''

    #meetup String collects all meetup data out of the 3 lists and stores the result
    meetup_string : str = ''

    # use a for loop to fill the lists with values,
    # for loop needs to run as often as count
    for x in range(count):
    
        # add values to the lists
        result = json_string.split(n1)[1].split(n2)[0]
        name_list.append(result)
        meetup_string = meetup_string + 'Name: ' + result + '\n'

        result = json_string.split(r1)[1].split(r2)[0]
        region_list.append(result)
        meetup_string = meetup_string + 'Region: ' + result + '\n'
        print('add region_list value ' + result)

        result = json_string.split(url1)[1].split(url2)[0]
        url_list.append(result)
        meetup_string = meetup_string + 'URL: ' + result + '\n' + '\n'
        
        
        if x == 0:
            length : int = len(name_list[x]) + len(region_list[x]) + len(url_list[x]) + 23
        else:
            n1 = ', name: '
            length : int = len(name_list[x]) + len(region_list[x]) + len(url_list[x]) + 25
        
        # trim string until all used meetups are no longer included
        for y in range(length):
            json_string = json_string[:0] + json_string[0 + 1:]

    context.bot.send_message(chat_id=update.message.chat_id, text=meetup_string)


        


