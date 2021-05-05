import os
from typing import Optional
from bot import run
import config

# Main entrypoint
def main():

    bot_token: Optional[str] = None

    try:
        bot_token = os.environ['BOT_TOKEN']
    except KeyError:
        print('The environment variable BOT_TOKEN is not defined')
        exit(1)

    try:
        config.TAPROOT_WATCH_URL = os.environ['TAPROOT_WATCH_URL']
    except KeyError:
        # Use default defined in config
        pass

    run(bot_token)


if __name__ == "__main__":
    main()