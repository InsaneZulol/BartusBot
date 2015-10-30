__author__ = 'Karol'

import urllib2
import datetime
import threading
import time
from bs4 import BeautifulSoup

class Plan(object):
    """
    Klasa Plan do obslugi planu

    Zawiera pola: [string]plan_url, [list]godziny, [list]lekcje
    Zawiera metody: pobierz_godziny, pobierz_lekcje, lekcje_dzien, lekcja_godzina, nastepna lekcja
    """
    def __init__(self):
        self.plan_url = "http://www.sci.edu.pl/plan/plany/o12.html"
        self.godziny = self.pobierz_godziny()
        self.lekcje = self.pobierz_lekcje()

    def pobierz_godziny(self):
        """
        Metoda pobiera godziny z strony planu i zwraca w postaci listy
        :return:[list] godziny
        """
        godziny = []

        page = urllib2.urlopen(self.plan_url)
        soup = BeautifulSoup(page.read())
        godziny_t=soup.findAll('td',{'class':'g'})

        for godzina_t in godziny_t:
            godzina_t_start = godzina_t.string[:godzina_t.string.find("-")]
            godzina_t_stop = godzina_t.string[godzina_t.string.find("-"):]

            # Czyszczenie stringow z godzinami
            # Usuwanie spacji i myslnikow rozdzielajacych godziny
            godzina_t_stop = godzina_t_stop.replace("-", "")
            godzina_t_stop = godzina_t_stop.replace("-", " ")
            godzina_t_start = godzina_t_start.replace("-", " ")

            godzina_t = [godzina_t_start, godzina_t_stop]
            godziny.append(godzina_t)

        return godziny

    def pobierz_lekcje(self):
        """
        Metoda pobiera plan/lekcje ze strony planu i zwraca w postaci listy
        :return:[list]lekcje
        """
        plan = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]      # Przesadzone TODO znalezc inne rozwiazanie
        godzina = 0

        page = urllib2.urlopen(self.plan_url)
        soup = BeautifulSoup(page.read())
        wiersze=soup.findAll('tr')

        for wiersz in wiersze:
            dzien = 0
            wiersz=wiersz.findAll('td',{'class':'l'})
            for lekcja in wiersz:
                lekcja = lekcja.findAll('span', {'class':'p'})
                if(len(lekcja)==0):
                    plan[godzina].append("")
                for przedmiot in lekcja:
                    plan[godzina].append(przedmiot.string)
                dzien += 1
            godzina += 1

        plan = plan[3:13]
        return plan

    def lekcje_dzien(self, dzien):
        """
        Funkcja zwraca wiadomosc z lista lekcji dla danego dnia
        :param dzien: Numer dnia od 0 do 4. Jezeli wartosc jest wieksza od 4 to przyjmuje wartosc 0, czyli poniedzialek
        :return: Wiadomosc w postaci stringa z lekcjami dla danego dnia
        """

        # Zapobiega odwolywania sie do nieistniejacego indexu
        # Nie mamy w planie danych dla dnia wyzej niz piatek
        if dzien > 4:
            dzien = 0

        wynik = ""
        index = 0

        for i in range(0,10):
            lekcja = self.lekcje[i][dzien]
            wynik += self.godziny[index][0] + "-" + self.godziny[index][1] + ": " + lekcja + "\r\n"

            # To kod w przypadku gdy beda okienka w planie
            """
            if len(lekcja)>0:
                wynik += self.godziny[index][0] + "-" + self.godziny[index][1] + ": " + lekcja + "\r\n"
            elif i>3:
                if len(self.lekcje[i-1][numer])>0:
                    wynik += self.godziny[index][0] + "-" + self.godziny[index][1] + ": " + lekcja + "\r\n"
            """

            index += 1
        return wynik

    def lekcja_godzina(self, nr_lekcji, dzien):
        """
        Zwraca nazwe przedmiotu dla podanej godziny (nr lekcji: od 0 do 9) i dnia
        :param nr_lekcji: numer lekcji w przedziale <0;9>
        :param dzien: numer dnia w przedziale <0;4>
        :return:string: nazwa przedmiotu
        """

        # Zapobiega odwolywania sie do nieistniejacego indexu
        if dzien > 4:
            dzien = 0

        # Zapobiega odwolywania sie do nieistniejacego indexu
        # Nie mamy w planie danych dla godziny wiecej niz 10tej
        if nr_lekcji > 9:
            nr_lekcji = 0

        return self.lekcje[nr_lekcji][dzien]

    def nastepna_lekcja(self, data):
        """
        Metoda zwracajaca nastepna lekcje i jej godziny w postaci wiadomosci string
        :param data: data najlepiej w postaci datetime.datetime.now()
        :return: string: wiadomosc skladajaca sie z nastepnej lekcji i jej godzin
        """

        godzina = data.hour
        minuta = data.minute
        dzien = data.weekday()

        # Zapobiega odwolywania sie do nieistniejacego indexu
        if dzien > 4:
            dzien = 0

        for i in range(len(self.godziny)):
            godzina_r = self.godziny[i][0]
            godzina_t = int(godzina_r[:godzina_r.find(":")])
            minuta_t = int(godzina_r[godzina_r.find(":")+1:])

            if (godzina < godzina_t) or (godzina == godzina_t and minuta <= minuta_t):
                lekcja = self.lekcja_godzina(i, dzien)
                if len(lekcja)>0:
                    return self.godziny[i][0] + " - " + self.godziny[i][1] + " " + lekcja

        # Jeszcze raz tym razem bez sprawdzania godziny
        # Zwracamy pierwsza lekcje nastepnego dnia
        for i in range(len(self.godziny)):
            lekcja = self.lekcja_godzina(i, dzien+1)
            if len(lekcja)>0:
                return self.godziny[i][0] + " - " + self.godziny[i][1] + " " + lekcja

        return "Jak ty to zrobiles?"

def every_seconds(seconds, function):
    """
    Funkcja wykonujaca inna funkcje co iles sekund

    :param seconds:
    :param function:
    :return:
    """

    function()
    threading.Timer(seconds, every_seconds, [seconds, function]).start()