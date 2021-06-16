import os
from bot import run
import config

# Main entrypoint
def main():

    try:
        bot_token = os.environ['BOT_TOKEN']
    except KeyError:
        print('The environment variable BOT_TOKEN is not defined')
        exit(1)

    try:
        config.MEMPOOL_SPACE_URL = os.environ['MEMPOOL_SPACE_URL']
    except KeyError:
        # Use default defined in config
        pass

    try:
        config.USE_WEBHOOK = True if str.lower(os.environ['USE_WEBHOOK']) == 'true' else False
        if config.USE_WEBHOOK:
            try:
                config.WEBHOOK_URL = os.environ['WEBHOOK_URL']
                config.WEBHOOK_PORT = int(os.environ['WEBHOOK_PORT'])
            except KeyError:
                print('If USE_WEBHOOK is true, you also need to supply WEBHOOK_URL and WEBHOOK_PORT')
                exit(1)
    except KeyError:
        # Use default defined in config
        pass

    try:
        config.FEATURE_ATH = True if str.lower(os.environ['FEATURE_ATH']) == 'true' else False
        if config.FEATURE_ATH:
            try:
                config.FEATURE_ATH_CHAT_ID = int(os.environ['FEATURE_ATH_CHAT_ID'])
            except KeyError:
                pass
            try:
                config.FEATURE_ATH_MANUAL_LAST_ATH = float(os.environ['FEATURE_ATH_MANUAL_LAST_ATH'])
            except KeyError:
                pass
    except KeyError:
        # Use default defined in config
        pass

    run(bot_token)


if __name__ == "__main__":
    main()