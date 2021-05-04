# Einundzwanzig Community Bot

Einundzwanzig Community Telegram Bot

## Requirements

* Python 3.8+
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library
* A Telegram Bot token, can be retrieved from [Bot Father](https://core.telegram.org/bots#6-botfather)

## Local development and deployment

You can create a Python3 virtual environment using

```shell
python3 -m venv env # Install virtual environment
source env/bin/activate # Activate virtual environment
pip install -r requirements.txt # Install dependencies
```

Make sure your virtual environment is activated every time you run the bot.
You can get out of the virtual environment by running `deactivate` inside the environment.

Afterwards you can run the bot with
```python
BOT_TOKEN=*** python src/main.py
```

The bot will start up and automatically receive updates and respond to messages.

## Docker

You can also use docker for local development and/or deployment, see the 
`Dockerfile` and `docker-compose.yml` for details
