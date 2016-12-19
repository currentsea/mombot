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
from config import api_hostname

# Get Version From File
from version import version

# Telegram Imports
from telegram.ext import Filters
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler

execute_ban_url = api_hostname + '/api/1.0/telegram/ban'
banlist_url = api_hostname + '/api/1.0/telegram/ban_list'

def getRedis(host=redis_host, port=6379, db=0, fake=False):
    if fake == True:
        r = fakeredis.FakeStrictRedis(host=host, port=port, db=db)
    else:
        r = redis.StrictRedis(host=host, port=port, db=db)
    return r



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
        usertarg = self.get_usertarg(update)
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
                params['username'] = usertarg
                params['chat_id'] = update.message.chat_id

                user_id = self.get_telegram_user_id(usertarg.replace(' ', '_'))
                if user_id != None:
                    params['target_ban_telegram_id'] = user_id
                    params['user_id'] = user_id
                    self.kick(bot, params)
                else:
                    bot.sendMessage(chat_id=update.message.chat_id, text='The user ' + usertarg + " has been added to the ban list successfully but will not be kicked from the room as they are currently not a member of it ")

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
        print ('target key = tg:users:' + target)
        idCall = r.get('tg:users:' + target)
        if idCall == None:
            return None
        else:
            return idCall.decode('utf-8')

    def get_usertarg(self, update):
        usertarg = update.message.text
        usertarg = usertarg.replace("/banhammer ", "")
        usertarg = usertarg.strip()
        print (usertarg)

        # if len(splitter) == 3:
        #     usertarg = splitter[1] + splitter[2]
        # elif len(splitter) == 2:
        #     usertarg = splitter[1]
        #  # splitter_smaller = splitter[1,len(splitter)]
        # # usertarg = ''
        # # count = 0
        # # for thing in splitter_smaller:
        # #     thing = thing.split()
        # #     usertarg = usertarg + ' ' + thing.strip()
        # #     # count = count + 1
        # # usertarg = splitter.strip()
        usertarg = usertarg.replace("@", "")
        return usertarg

    def is_banned(self, bot, update):
        usertarg = self.get_usertarg(update)

        #
        # usertarg = splitter[1]
        # usertarg = usertarg.rstrip()
        # usertarg = usertarg.replace("@", "")
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

    def get_username(self, update):
        user_id = update.message.new_chat_member.id
        username = update.message.new_chat_member.first_name
        if update.message.new_chat_member.last_name != '' and update.message.new_chat_member.last_name != None:
            username = username + " " + update.message.new_chat_member.last_name
        else:
            username = user_id
        return username

    def process_event(self, bot, update):
        print (update.message)
        username = None
        event_map = self.get_event_map(update)

        try:
            username = update.message.new_chat_member.username
            user_id = update.message.new_chat_member.id
            event_map['target_user_id'] = user_id
            if username == '':
                username = self.get_username(update)
            bot.sendMessage(chat_id=update.message.chat_id, text='The user ' + username + ' (USER ID: ' + user_id  + ') is not on the banlist. Welcome!')
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
        event_map['target_username'] = username

        print (event_map)
        self.cache_event_map(event_map)

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

        if "target_username" in event_map and "target_user_id" in event_map:
            username = event_map['target_username'].replace(' ', '_')
            user_id = event_map['target_user_id']

        else:
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
        headers = {}
        headers['X-Ban-Hammer-Key'] = banhammer_key
        headers['X-Ban-Hammer-Secret'] = banhammer_secret
        headers['Content-Type'] = 'x-www-form-urlencoded'
        req = requests.post('https://api.telegram.org/bot' + token + '/kickChatMember', headers=headers, params=params, verify=False)
        if req.status_code < 400:
            bot.sendPhoto(chat_id=params['chat_id'],
                          photo='http://i0.kym-cdn.com/photos/images/newsfeed/000/024/724/ban_hammer.jpg')
            target_text = 'Banhammer has perma-banned ' + params['username'] + ' no kittens were harmed in this process. Get away from our bitcoin you filthy scoundrels!'
        else:
            target_text = 'Something went horribly wrong, contact @currentsea to fix this immediately! ERROR CODE: ' + str(req.status_code)
        bot.sendMessage(chat_id=params['chat_id'], text=target_text)
    def helper(self, bot, update):
        bot.sendMessage(chat_id=update.message.chat_id, text="   MomBot v" + version +"   \n---COMMANDS----\n/start@bitcoin_mom_bot - initializes the bot\n/banhammer <telegram_handle> - banhamers the given handle\n/is_banned <telegram_handle> - lets you know whether the <telegram_handle> is on the ban list")

if __name__ == "__main__":
    MomBot()
