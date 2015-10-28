﻿import StringIO
import json
import logging
import random
import urllib
import urllib2
import requests
import facebook
import warnings


# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

warnings.filterwarnings('ignore', category=DeprecationWarning) # dałem to, bo moduł facebook jest troche stary i wyskakują błędy i moze pomoze
#TOKEN TELEGRAMA NIE DOTYKAC PEDAŁY XD
TOKEN = '129060792:AAGFH7v-zyS-PfX1I_-FOSIvm6vAAH9Yi-U'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

#app_secret = '417a9e046897e14bb66eac1c3f1c7451'
#app_id = '985465174848513'


#TOKEN REQUEST HHTPS

httpsTokenRequest = 'https://graph.facebook.com/oauth/access_token?client_id=985465174848513%20&client_secret=417a9e046897e14bb66eac1c3f1c7451&grant_type=client_credentials'
r = requests.get(httpsTokenRequest)

access_token = r.text.split('=')[1]
graph = facebook.GraphAPI(access_token)

urlLastMessage = 'https://graph.facebook.com/film.czeski/feed?fields=id&limit=1&access_token=' + access_token
response = requests.get(urlLastMessage)
decoded_json_data = response.json()
postNode = graph.get_object(id = decoded_json_data["data"][0]["id"])



#TODO: To pobiera obrazek, teraz tylko zeby telegram umiał to odczytac na chacie.
urlLastPicture = 'https://graph.facebook.com/film.czeski/feed?fields=full_picture&limit=1&access_token=' + access_token
responsePIC = requests.get(urlLastPicture)
decoded_json_PICDATA = responsePIC.json()
postNodePIC = decoded_json_PICDATA["data"][0]["full_picture"]


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
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

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
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue())
            elif text == '/news':
<<<<<<< HEAD
                reply(postNode['message'], postNodePIC)
=======
                reply(postNode['message'])
>>>>>>> origin/master
            else:
                reply('What command?')

        # CUSTOMIZE FROM HERE
        
        

        elif 'who are you' in text:
            reply('telebot starter kit, created by yukuku: https://github.com/yukuku/telebot')
        elif 'wojna' in text:
            reply('wojna gej')
        elif 'cesky' in text:
            reply(postNodePIC)


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
