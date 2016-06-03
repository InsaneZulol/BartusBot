# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import StringIO
import json
import logging
import random
import urllib
import urllib2
import utils
import parsedatetime
from time import mktime
from datetime import datetime, timedelta
import reminderStore
import responses_utils

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# Glowne zmienne
plan = utils.Plan()                     # Obsluga planu
reminder = reminderStore                # Obsluga przypomnien
response = responses_utils.Responses()
#facebook = facebook_utils.Facebook()   # Obsluga facebooka
luck_level = 2                          # W przedziale od 0 do 100 im wiecej tym czesciej glupie odpowiedzi


#warnings.filterwarnings('ignore', category=DeprecationWarning)  # Ignorowanie bledow o przestarzalych funkcjach - do facebooka

# Token telegrama
TOKEN = '129060792:AAGFH7v-zyS-PfX1I_-FOSIvm6vAAH9Yi-U'
BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

def luck_sim(msg):
    luck = random.randint(0,100)
    if luck > luck_level:
        return msg
    else:
        return plan.unlucky

def send_smth():
    for chat in plan.chats:
        msg = random.choice(plan.odpowiedzi)
        resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
            'chat_id': str(chat),
            'text': msg.encode('utf-8'),
            'disable_web_page_preview': 'true',
        })).read()

# ================================
class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

# ================================
def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

# ================================
class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))

class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))

class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']

        # Po aktualizacji w maju 2016 bot czasami dostaje edytowane wiadomosc
        # ma to miejsce gdy ktos szybciej zedytuje niz bot otrzymuje wiadomosc
        try:
            message = body['message']
        except:
            message = body['edited_message']
        message_id = message.get('message_id')
        date = message.get('date')
        _date_income = datetime.fromtimestamp(int(date))
        try:
            text = message.get('text').decode("utf-8")
        except:
            text = message.get('text')
        fr = message.get('from')
        user_id = fr['id']

        try:
            nickname = fr['username']
        except:
            nickname = ""

        try:
            first_name = fr['first_name']
        except:
            first_name = ""

        try:
            last_name = fr['last_name']
        except:
            last_name = ""
        user_name = first_name.decode("utf-8") + " " + last_name.decode("utf-8")
        chat = message['chat']
        chat_id = chat['id']
        try:
            chat_name = chat['title'].decode("utf-8")
        except:
            chat_name = ""

        # Zapisywanie wszystkich wiadomosci na serwer
        if text != "":
            try:
                reminderStore.putLogRow(str(chat_id).decode('utf8'), str(user_id).decode('utf8'), str(user_name).decode('utf8'), str(chat_name).decode('utf8'), _date_income, str(text).decode('utf8'), str(nickname).decode('utf8'))
            except:
                logging.error("Nie udalo sie zapisac wiadomosci")

        # Zbieranie wszystkich chat_id
        if chat_id not in plan.chats:
            plan.chats.append(chat_id)

        def reply(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)
        if text:
            if text.startswith('/'):
                reply(response.getReplyForCommand(text, chat_id, message_id))
            elif text.startswith('you\'re') or text.startswith('youre') or text.startswith('You\'re') or text.startswith('Youre') or text.startswith('you are') or text.startswith('You are'):
                reply("For You")

class ReminderTask(webapp2.RequestHandler):
    def get(self):
        try:
            expired_rows = reminderStore.getExpiredRows()
            logging.info("Reminder task")
        except:
            expired_rows = []
            logging.info("Failed getting data in reminder")

        for row in expired_rows:
            logging.info("Chat enabled:" + str(getEnabled(row.chat_id)))
            error = False
            _chat_id = str(row.chat_id)
            try:
                _msg = str(row.msg)
                _msg = unicode(_msg)
            except:
                logging.info("Error with parsing _msg or _chat_id")
                reminderStore.deleteRemind(row)
                _msg = "Prawilnie przypominam"

            try:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(_chat_id),
                    'text': _msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(row.msg_id),
                })).read()
                logging.info("Chan enabled:" + str(getEnabled(row.chat_id)))
                reminderStore.deleteRemind(row)
            except:
                logging.info("Error in sending")

class WeekStatsTask(webapp2.RequestHandler):
    def get(self):
        for chat_id in plan.chats:
            try:
                stats = reminderStore.getWeekStats(str(chat_id))
                #msg = "Liczone od: 30 stycznia 2017, 17:00 \r\n"
                msg = "User   :   number of messages  :   %\r\n"
                msg += "----------------------------------"
                count = 0
                for row in stats:
                    count += row[1]
                for row in stats:
                    percentage = (float(row[1])/float(count))*100.0
                    msg += "\r\n" + str(row[0]) + "  :  " + str(row[1]) + "  :  " + str(round(percentage,2)) + "%"
            except:
                msg = "Statystyki nie sa dostepne"

            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'disable_web_page_preview': 'true',
            })).read()

        reminderStore.resetWeekStats()

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/remindertask', ReminderTask),
    ('/weekstats', WeekStatsTask),
], debug=True)
