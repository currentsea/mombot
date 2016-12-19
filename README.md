# mombot
Telegram bot for https://bitcoin.mom -- helps prevent scammers

# Setup
* Acquire a telegram token for your bot deployment by following the Telegram provided instructions at this URL: https://core.telegram.org/bots#6-botfather
* Place the token you acquired in the step above into the value of `token`, `banhammer_key`, and `banhammer_secret` in the `credentials_example.py` file and rename it to `credentials.py` by running `cp credentials_example.py credentials.py`
* Place the the location of your redis host in `config_exapmle.py` and copy to `config.py` by running `cp config_example.py config.py`
<<<<<<< HEAD
=======
* You need redis installed and configured properly, you wll connect to a redis store for this bot to work
* Make sure you test the bot within a `virtualenv` that you create by installing the requirements located in `reuirements.txt` with `pip install -r requirements.txt` from within your virtualenv
>>>>>>> be273e5... fix

# Bot Tokens
* To run this bot independently, you'll need your own token and bot username which can be acquired by following the instructions on the Telegram page located here: *https://core.telegram.org/bots#6-botfather*
* Additionally, You'll need a `BANHAMMER_SECRET` and `BANHAMMER_TOKEN` token for this bot to properly function with the blacklist located at *https://bitcoin.mom* - these are currently only given to a select number of individuals.
* If you would like to request your own `BANHAMMER_SECRET` and `BANHAMMER_TOKEN` please send a message to me on keybase:
