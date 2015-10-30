__author__ = 'jupiter'

import facebook
import requests


class Facebook(object):
    def __init__(self):
        self.httpsTokenRequest = 'https://graph.facebook.com/oauth/access_token?client_id=985465174848513%20&client_secret=417a9e046897e14bb66eac1c3f1c7451&grant_type=client_credentials'
        self.r = requests.get(self.httpsTokenRequest)
        self.access_token = self.r.text.split('=')[1]
        self.graph = facebook.GraphAPI(self.access_token)
        self.url_last_post = ""

        self.get_last_post()

    def get_last_post(self):
        self.url_last_post = 'https://graph.facebook.com/film.czeski/feed?fields=id&limit=1&access_token=' + self.access_token
        self.responseMSG = requests.get(self.url_last_post)
        self.decoded_json_MSGDATA = self.responseMSG.json()
        self.postNode = self.graph.get_object(id = self.decoded_json_MSGDATA["data"][0]["id"])