#!/usr/local/bin/python3
# Author: Joseph "currentsea" Bull
# License: LGPL 3.0

import os
import json
import time
import uuid
import redis
import logging
import requests
import fakeredis

# Token Imports
from credentials import token
from credentials import banhammer_key
from credentials import banhammer_secret

# Config vals
from config import redis_host

# Get Version From File
from version import version

# Telegram Imports
from telegram.ext import Filters
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler

api_hostname = 'https://localhost:5000'
execute_ban_url = api_hostname + '/api/1.0/telegram/ban'
banlist_url = api_hostname + '/api/1.0/telegram/ban_list'

def getRedis(host=redis_host, port=6379, db=0, fake=False):
    if fake == True:
        r = fakeredis.FakeStrictRedis(host=host, port=port, db=db)
    else:
        r = redis.StrictRedis(host=host, port=port, db=db)
    return r

def cache_telegram_event(keygen):
    try:
        prefix = "tg"
        try:
            prefix = prefix + ":" + keygen.chat.type + ":" + keygen.chat.title
        except:
            prefix = prefix + ":misc:" +  generate_cache_key()

        r = getRedis()
        print('caching heavily')
        for key in keygen:
            if type(keygen[key]) is dict:
                print (keygen[key])
                if key == "new_chat_member":
                    r.hmset(prefix + ":users:" + keygen[key]['username'], keygen[key])
                    r.sadd(prefix + ":users_detail", keygen[key])
                    r.sadd(prefix + ":user_handles", keygen[key]['username'])
                    r.sadd(prefix + ":user_identifiers", keygen[key]['id'])
                else:
                    r.sadd(prefix + ":" + key, keygen[key])
    except:
        print ('CACHING EVENT FAILED')

def generate_cache_key():
     the_time = str(time.time())
     the_uuid = str(uuid.uuid4())[0:18].replace("-", "")
     the_time = the_time[0:the_time.rfind(".")]
     print (the_time)
     return the_time + "-" + the_uuid

class MomBot():
    def __init__(self):
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self.help_handler = CommandHandler('help', self.helper)
        self.start_handler = CommandHandler('start', self.start)
        self.ban_hammer_handler = CommandHandler('banhammer', self.banhammer)
        self.is_user_banned_handler = CommandHandler('is_banned', self.is_banned)
        self.summarize_handler = MessageHandler([], self.process_event)
        self.dispatcher.add_handler(self.help_handler)
        self.dispatcher.add_handler(self.start_handler)
        self.dispatcher.add_handler(self.ban_hammer_handler)
        self.dispatcher.add_handler(self.is_user_banned_handler)
        self.dispatcher.add_handler(self.summarize_handler)
        self.updater.start_polling()
        self.cache_connection = getRedis()

    def start(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="MomBot has come online!")

    def banhammer(self, bot, update):
        usertarg = update.message.text
        splitter = usertarg.split(" ")
        usertarg = splitter[1]
        usertarg = usertarg.rstrip()
        usertarg = usertarg.replace("@", "")
        blacklist = self.get_blacklist()
        if usertarg in blacklist:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text='We have already banhammered ' + str(usertarg))
        else:
            if usertarg.lower() == "currentsea" or usertarg.lower() == "mrjozza" or usertarg.lower() == "aztek_btc":
                bot.sendMessage(chat_id=update.message.chat_id, text='Fuck off.')
            else:
                headers = self.get_banhammer_headers()
                event_map = self.get_event_map(update)
                params = {}
                params['target_ban_username'] = usertarg
                params['administrator_username'] = event_map['from_user_username']
                params['administrator_telegram_id'] = event_map['from_user_id']
                user_id = self.get_telegram_user_id(usertarg)
                if user_id != None:
                    params['target_ban_telegram_id'] = user_id
                # try:
                #     params['target_ban_telegram_id'] = update.
                bot.sendMessage(chat_id=update.message.chat_id, text='Placeholder!')
                req = requests.post(execute_ban_url, headers=headers, verify=False, data=json.dumps(params))

                if req.status_code < 400:
                    bot.sendPhoto(chat_id=update.message.chat_id, photo='http://i0.kym-cdn.com/photos/images/newsfeed/000/024/724/ban_hammer.jpg')
                    bot.sendMessage(chat_id=update.message.chat_id, text='The user ' + usertarg + " has been added to the ban list successfully. ")
                else:
                    bot.sendMessage(chat_id=update.message.chat_id, text='Unable to successfully add ' + usertarg + ' to the ban list. HTTP Response: ' + str(req.status_code))

    def get_telegram_user_id(self, target):
        r = getRedis()
        idCall = r.get('tg:users:' + target)
        if idCall == None:
            return None
        else:
            return idCall.decode('utf-8')

    def is_banned(self, bot, update):
        usertarg = update.message.text
        splitter = usertarg.split(" ")
        usertarg = splitter[1]
        usertarg = usertarg.rstrip()
        usertarg = usertarg.replace("@", "")
        blacklist = self.get_blacklist()
        if usertarg not in blacklist:
            bot.sendMessage(chat_id=update.message.chat_id, text=str(usertarg + ' is not on the ban list. type /banhammer ' + usertarg + ' to banhammer them'))
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text=str(usertarg + ' is on the blacklist!  Keep this asshole out of your channel!!!'))

    def get_banhammer_headers(self):
        headers = {}
        headers['Content-Type'] = 'application/json'
        headers['X-Ban-Hammer-Key'] = banhammer_key
        headers['X-Ban-Hammer-Secret'] = banhammer_secret
        return headers

    def get_blacklist(self, blacklist_api_url=banlist_url):
        headers = self.get_banhammer_headers()
        req = requests.get(blacklist_api_url, headers=headers, verify=False)
        blacklist_users = req.json()['ban_list']
        blacklist = []
        for user in blacklist_users:
            blacklist.append(user['banned_user'])
        return blacklist

    def process_event(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text='Processing')
        username = None
        try:
            username = update.message.new_chat_member.username
        except:
            pass
        if username != None:
            blacklist = self.get_blacklist()
            if username in blacklist:
                params = {}
                params['chat_id'] = update.message.chat_id
                params['user_id'] = update.message.new_chat_member.id
                params['username'] = username
                self.kick(bot, params)
            else:
                bot.sendMessage(chat_id=update.message.chat_id, text='The user ' + username + ' is not on the banlist. Welcome!')
        event_map = self.get_event_map(update)
        print (event_map)
        self.cache_event_map(event_map)
        bot.sendMessage(chat_id=update.message.chat_id, text='Processed')

    def get_event_map(self, update):
        event_map = {}
        update_message = update.message.__dict__
        for item in update_message:
            if item == 'chat' or item == 'from_user' or item == "new_chat_member":
                try:
                    iterator = update_message[item].__dict__
                    for chatitem in iterator:
                        event_map[item + "_" + chatitem] = iterator[chatitem]
                except:
                    pass
            else:
                event_map[item] = update_message[item]
        return event_map

    def cache_event_map(self, event_map):
        print ('begin map caching')
        try:
            username =  event_map['new_chat_member_username']
            user_id = event_map['new_chat_member_id']
        except:
            username = event_map['from_user_username']
            user_id = event_map['from_user_id']
        updates_key = 'tg:' + event_map['chat_title'] + ":updates"
        event_key = updates_key + ":" + str(uuid.uuid4())[0:8]
        users_key = 'tg:' + event_map['chat_title'] + ":users"
        self.cache_single_event(event_key, event_map)
        self.cache_event_list(updates_key, event_key)
        self.cache_telegram_user(users_key, username, user_id)
        pass

    def cache_telegram_user(self, key, user_handle, user_id):
        r = getRedis()
        target_list = []
        target_list.append(user_handle)
        target_list.append(user_id)
        r.set('tg:users:' + user_handle, user_id)
        r.sadd(key, target_list)
        print ('Added ' + user_handle + ' to ' + key)

    def cache_event_list(self, key, val):
        r = getRedis()
        r.lpush(key, val)
        print ('Added ' + str(val) + ' to ' + str(key))

    def cache_single_event(self, target_key, event_map):
        print ('Caching a single event')
        r = getRedis()
        r.hmset(target_key, event_map)
        print ('Set ' + target_key + " successfully!")

    def kick(self, bot, params):
        headers = self.get_banhammer_headers()
        req = requests.post('https://api.telegram.org/' + token +'/kickChatMember', headers=headers, params=params, verify=False)
        if req.status_code < 400:
            bot.sendPhoto(chat_id=params["chat_id"], photo='http://i0.kym-cdn.com/photos/images/newsfeed/000/024/724/ban_hammer.jpg')
            bot.sendMessage(chat_id=params["chat_id"], text='Banhammer has perma-banned ' + params['username'] + ' no kittens were harmed in this process. Get away from our bitcoin you filthy scoundrels!')
        else:
            bot.sendMessage(chat_id=params['chat_id'], text='Something went horribly wrong, contact @currentsea to fix this immediately!')

    def helper(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="   MomBot v" + version +"   \n---COMMANDS----\n/start@bitcoin_mom_bot - initializes the bot\n/banhammer <telegram_handle> - banhamers the given handle\n/is_banned <telegram_handle> - lets you know whether the <telegram_handle> is on the ban list")

if __name__ == "__main__":
    MomBot()
