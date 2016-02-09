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
import requests
import facebook_utils
import warnings
import datetime
import utils
import threading
import time
import parsedatetime
import pytz
from pytz import timezone
from time import mktime
from datetime import datetime, timedelta
from google.appengine.api import taskqueue

from google.appengine.api import taskqueue
import reminderStore

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

# Glowne zmienne
plan = utils.Plan()                     # Zmienna dla obslugi planu
#facebook = facebook_utils.Facebook()    # Zmienna dla obslugi facebooka
luck_level = 2                          # W przedziale od 0 do 100 im wiecej tym czesciej glupie odpowiedzi
reminder = reminderStore
POMOC = """Nazywaja mnie @BartusBot. Jestem tu aby smieszkowac.

Mozesz mnie kontrolowac uzywajac tych komend:

/pon - Plan na poniedzialek
/wt - Plan na wtorek
/sr - Plan na srode
/cz - Plan na czwartek
/pt - Plan na piatek
/j - Plan na jutro
/n - Nastepna nastepna nastepna
/d - Plan na dzisiaj

/remind data "wiadomosc" - przypomninanie
data w formacie:

    August 25th, 2008
    25 Aug 2008
    Aug 25 5pm
    5pm August 25
    next saturday
    tomorrow
    next thursday at 4pm
    at 4pm
    eod
    tomorrow eod
    eod tuesday
    eoy
    eom
    in 5 minutes
    5 minutes from now
    5 hours before now
    2 hours before noon
    2 days from tomorrow

/stats - wyswietla statystyki czatu

/weekstats - wyświetla statystyki czatu liczone od poprzedniej niedzieli

Mozesz tez uzywac wydluzonych komend, np, /dzisiaj, /poniedzialek, /nastepna, /jutro itd."""

warnings.filterwarnings('ignore', category=DeprecationWarning) # dałem to, bo moduł facebook jest troche stary i wyskakują błędy i moze pomoze

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

# def every_seconds_custom(seconds):
#     threading.Timer(seconds, every_seconds_custom, [seconds, send_smth]).start()
#     logging.info('EVERY SECONDS!')


#taskqueue.add(url='/service', params={'user': user}, method="GET")

# every_seconds_custom(2)

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
        message = body['message']
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


        # logging
        #logging.info("Author: " + fr + ". Chat: " + chat + ", id: " + chat_id)
        if text != "":
            try:
                reminderStore.putLogRow(str(chat_id).decode('utf8'), str(user_id).decode('utf8'), str(user_name).decode('utf8'), str(chat_name).decode('utf8'), _date_income, str(text).decode('utf8'), str(nickname).decode('utf8'))
            except:
                logging.error("Nie udalo sie zapisac wiadomosci")

        if chat_id not in plan.chats:
            plan.chats.append(chat_id)

        if not text:
            logging.info('no text')
            return


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

        if text.startswith('/'):
            if user_id == '166719489':
                reply('Pedalom nie pomagam')
            elif text == '/start bartusbot' or text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop bartusbot' or text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            # elif text == '/news@BartusBot' or text == '/news':
            #     ##img = facebook.get_last_image()
            #     img = Image.new('RGB', (512, 512))
            #     base = random.randint(0, 16777216)
            #     pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
            #     img.putdata(pixels)
            #     output = StringIO.StringIO()
            #     img.save(output, 'JPEG')
            #     if img:
            #         reply(facebook.get_last_post()['message'])
            #         reply(reply(img=output.getvalue()))
            #     else:
            #         reply(facebook.get_last_post()['message'])

            elif text == '/test':
                msg = luck_sim(random.choice(plan.odpowiedzi))
                reply(msg)
            elif text == '/poniedzialek' or text == '/pon' or text == '/pon@BartusBot' :
                msg = luck_sim(plan.lekcje_dzien(0))
                reply(msg)
            elif text == '/wtorek' or text == '/wt' or text == '/wt@BartusBot':
                msg = luck_sim(plan.lekcje_dzien(1))
                reply(msg)
            elif text == '/sroda' or text == '/sr' or text == '/sr@BartusBot':
                msg = luck_sim(plan.lekcje_dzien(2))
                reply(msg)
            elif text == '/czwartek' or text == '/cz' or text == '/cz@BartusBot':
                msg = luck_sim(plan.lekcje_dzien(3))
                reply(msg)
            elif text == '/piatek' or text == '/pt' or text == '/pt@BartusBot':
                msg = luck_sim()
                reply(plan.lekcje_dzien(4))
            elif text == '/jutro' or text == '/j' or text == '/j@BartusBot':
                msg = plan.lekcje_dzien(datetime.now().weekday()+1)
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/nastepna' or text == '/n' or text == '/n@BartusBot':
                msg = plan.nastepna_lekcja()
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/dzisiaj' or text == '/d' or text == '/d@BartusBot':
                msg = plan.lekcje_dzien(datetime.now().weekday())
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/wczoraj' or text == '/wczoraj@BartusBot':
                reply(plan.lekcje_dzien(datetime.now().weekday()-1))
            elif text == '/sobota' or text == '/sobota@BartusBot':
                reply(random.choice(plan.odpowiedzi))
            elif text == '/niedziela' or text == '/niedziela@BartusBot':
                reply(random.choice(plan.odpowiedzi))
            elif text == '/help' or text == '/pomoc' or text == '/pomoc@BartusBot':
                reply(POMOC)
            elif text == '/wolaj' or text == "/wszyscy" or text == "/wolam" or text == '/wolaj@BartusBot' or text == '/wszyscy@BartusBot' or text == '/wolam@BartusBot':
                nicknames = reminderStore.getNicknames(chat_id)
                msg = "Wolam: "
                for nickname in nicknames:
                    msg += "@"+str(nickname) + " "
                reply(msg)
            elif text.startswith("/remind"):
                _msg_id = str(message_id)
                logging.info(_msg_id)
                try:
                    temp = text
                    temp = temp[temp.find(" ")+1:]
                    _date_temp = temp[:temp.find("\"")]
                    _msg = temp[len(_date_temp)+1:len(temp)-1]
                    if len(_msg) < 1:
                        _msg = "Prawilnie przypominam"
                    #_msg = temp[temp.find(" ")+1:]
                    _date = datetime.now()
                    _date_income = datetime.fromtimestamp(int(date))
                    _chat_id = str(chat_id)

                    cal = parsedatetime.Calendar()
                    cal.parse(_date_temp)

                    time_struct, parse_status = cal.parse(_date_temp)
                    _date = datetime.fromtimestamp(mktime(time_struct))
                    #_date, _ = cal.parseDT(datetimeString=_date_temp, tzinfo=pytz.timezone("Europe/Warsaw"))

                    reminderStore.putReminderRow(_chat_id, _date_income, _date, _msg, _msg_id)
                    #reply(str(_date) + ":" + _msg)
                    #reply(_msg + ":" + _date.strftime("%Y-%m-%d %H:%M:%S"))
                    reply("Spoko cumplu przypomne.")
                except:
                    reply("Cos sie zepsulo i nie bylo cie slychac")
                    logging.info("Error in /remind")
            elif text == '/stats' or text == '/stats@BartusBot':
                try:
                    stats = reminderStore.getStats(str(chat_id))

                    msg = "User   :   number of messages  :   %\r\n"
                    msg += "----------------------------------"
                    count = 0
                    for row in stats:
                        count += row[1]
                    for row in stats:
                        percentage = (float(row[1])/float(count))*100.0
                        msg += "\r\n" + str(row[0]) + "  :  " + str(row[1]) + "  :  " + str(round(percentage,2)) + "%"

                    msg += "\r\n----------------------------------"
                    msg += "\r\nLiczone od: 30 stycznia 2017, 17:00 \r\n"
                except:
                    msg = "Statystyki nie sa dostepne"

                reply(msg)

            elif text == '/weekstats' or text == '/weekstats@BartusBot':
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

                    msg += "\r\n----------------------------------"
                    msg += "\r\nLiczone od ostatniej niedzieli \r\n"
                except:
                    msg = "Statystyki nie sa dostepne"

                reply(msg)

            elif text.startswith('/stats'):
                #logging.info(text)
                try:
                    temp = text
                    _msg = temp[7:]
                    #logging.info("chat_id: \"" + _msg  + "\"")
                    #logging.info("chat_id: \"" + str(chat_id) + "\"")
                    if len(_msg) < 1:
                        _msg = "Bledny id"
                    stats = reminderStore.getStats(str(_msg))
                    msg = "Imie   :   ilosc wiadomosci  :   %\r\n"
                    msg += "----------------------------------"
                    count = 0
                    for row in stats:
                        count += row[1]
                    for row in stats:
                        percentage = (float(row[1])/float(count))*100.0
                        msg += "\r\n" + str(row[0]) + "  :  " + str(row[1]) + "  :  " + str(round(percentage,2)) + "%"
                    reply(msg)
                except:
                    reply("Statystyki sa niedostepne")

            elif text.startswith('/weekstats'):
                #logging.info(text)
                try:
                    temp = text
                    _msg = temp[7:]
                    #logging.info("chat_id: \"" + _msg  + "\"")
                    #logging.info("chat_id: \"" + str(chat_id) + "\"")
                    if len(_msg) < 1:
                        _msg = "Bledny id"
                    stats = reminderStore.getWeekStats(str(_msg))
                    msg = "Imie   :   ilosc wiadomosci  :   %\r\n"
                    msg += "----------------------------------"
                    count = 0
                    for row in stats:
                        count += row[1]
                    for row in stats:
                        percentage = (float(row[1])/float(count))*100.0
                        msg += "\r\n" + str(row[0]) + "  :  " + str(row[1]) + "  :  " + str(round(percentage,2)) + "%"
                    reply(msg)
                except:
                    reply("Tygodniowe statystyki sa niedostepne")

class ReminderTask(webapp2.RequestHandler):
    def get(self):
        #send_smth()
        try:
            expired_rows = reminderStore.getExpiredRows()
            logging.info("Reminder task")
        except:
            expired_rows = []
            logging.info("Failed getting data in reminder")

        for row in expired_rows:
            #logging.info(str(row.msg) + str(row.date))
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
    ('/reminderqueue', ReminderTask),
    ('/weekstats', WeekStatsTask),
], debug=True)
