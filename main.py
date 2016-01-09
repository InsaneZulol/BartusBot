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

def every_seconds_custom(seconds):
    threading.Timer(seconds, every_seconds_custom, [seconds, send_smth]).start()
    logging.info('EVERY SECONDS!')


#taskqueue.add(url='/service', params={'user': user}, method="GET")

every_seconds_custom(2)

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
    utils.every_seconds(5, send_smth)

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
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

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
            if text == '/start bartusbot' or text == '/start':
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
                msg = plan.lekcje_dzien(datetime.datetime.now().weekday()+1)
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/nastepna' or text == '/n' or text == '/n@BartusBot':
                msg = plan.nastepna_lekcja()
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/dzisiaj' or text == '/d' or text == '/d@BartusBot':
                msg = plan.lekcje_dzien(datetime.datetime.now().weekday())
                msg = luck_sim(msg)
                reply(msg)
            elif text == '/wczoraj':
                reply(plan.lekcje_dzien(datetime.datetime.now().weekday()-1))
            elif text == '/sobota':
                reply(random.choice(plan.odpowiedzi))
            elif text == '/niedziela':
                reply(random.choice(plan.odpowiedzi))
            elif text == '/help' or text == '/pomoc':
                reply(POMOC)
                send_smth()
            elif text == '/wszyscy':
                for chat in plan.chats:
                    #msg = random.choice(plan.odpowiedzi)
                    msg = "Chat id's: "
                    for chat_str in plan.chats:
                        msg += str(chat_str) + ", "

                    #msg = ';'.join(plan.chats)
                    resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id': str(chat),
                        'text': msg.encode('utf-8'),
                        'disable_web_page_preview': 'true',
                    })).read()
            elif text == '/test2':
                send_smth()

            elif text == '/przepraszam':
                msg = "Przepraszam"
                for chat in plan.chats:
                    resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id': str(chat),
                        'text': msg.encode('utf-8'),
                        'disable_web_page_preview': 'true',
                    })).read()

            elif text.startswith("/remind"):
                temp = text
                command = text[:text.rfind(" ")]
                _msg = text[text.rfind(" ")+1:]
                _date_temp = temp[:temp.rfind(" ")]
                _date_temp = _date_temp[temp.rfind(" "):]

                _msg_rep =  _msg + "\r\n" + _date_temp
                _date = datetime.datetime.now()
                _date_income = datetime.datetime.fromtimestamp(int(date))
                _chat_id = str(chat_id)

                reminderStore.putReminderRow(_chat_id, _date_income, _date, _msg)
                reply(_msg_rep)
            elif text == '/testremind':
                expired_rows = reminderStore.getExpiredRows()

                for row in expired_rows:
                    resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id': str(row.chat_id),
                        'text': row.msg.encode('utf-8'),
                        'disable_web_page_preview': 'true',
                    })).read()

                reminderStore.deleteReminds(expired_rows)

        # if random.randint(0,1000) < 2:
        #     reply(random.choice(plan.odpowiedzi))



app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
