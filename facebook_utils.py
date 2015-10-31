import facebook
import requests

class Facebook(object):
    """
    Klasa Facebook do obslugi facebooka

    Zawieta pola access_token, graph
    """
    def __init__(self):
        self.acces_token = self.get_acces_token()           # Pobieramy acces token
        self.graph = facebook.GraphAPI(self.access_token)

    def get_acces_token(self):
        """
        Zwraca acces token dla aplikacji
        :return:aacces_token
        """
        httpsTokenRequest = 'https://graph.facebook.com/oauth/access_token?client_id=985465174848513%20&client_secret=417a9e046897e14bb66eac1c3f1c7451&grant_type=client_credentials'
        r = requests.get(httpsTokenRequest)
        return  r.text.split('=')[1]

    def get_last_post(self):
        """
        Zwraca ostatni post
        :return:postNode - aby odniesc sie do zawartej wiadomosci (tresci) trzeba uzyc indeksu ['message'], np get_last_post()['message']
        """
        url_last_post = 'https://graph.facebook.com/film.czeski/feed?fields=id&limit=1&access_token=' + self.access_token
        responseMSG = requests.get(url_last_post)
        decoded_json_MSGDATA = responseMSG.json()
        postNode = self.graph.get_object(id = decoded_json_MSGDATA["data"][0]["id"])
        return postNode

    def get_last_image(self):
        """
        Zwraca ostanie zdjecie
        :return:postNodeIMG lub false w przypadku niepowodzenia
        """
        url_last_picture = 'https://graph.facebook.com/film.czeski/feed?fields=full_picture&limit=1&access_token=' + self.access_token
        try:
            responseIMG = requests.get(url_last_picture)
            decoded_json_IMGDATA = responseIMG.json()
            postNodeIMG = decoded_json_IMGDATA["data"][0]["full_picture"]
            return postNodeIMG
        except ValueError:
            return False