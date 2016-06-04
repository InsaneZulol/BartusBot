__author__ = 'Karol'

import urllib2
import datetime
import threading
import time
import logging
import json
from bs4 import BeautifulSoup

class Schedule(object):
    def __init__(self):
        self.url_path_to_schedule = "http://www.sci.edu.pl/plan/plany/o12.html"
        self.hours = self.downloadHoursFromWeb()
        self.time_table = self.downloadTimetableFromWeb()
        self.replies = [
            "Kuurwa spok",
            "Ty stara kurwo zmarnowałaś mi 25 lat zycia",
            "Trzymajcie go bo zaraz zacznie wyrywac kable",
            "Zapuszam dabstep",
            "Zapusc kurwa dabstep",
            "No w koncu pora sie najebac",
            "Kurwa spok miales jedna robote do wykonania ja pierdole",
            "Wypierdalaj z mojego statku",
            "Zjebales spok \r\n Zjebales kurwa",
            "Gdzie sa dziewczeta gdzie jest kurwa wodka co to jest za muzyka gdzie jest dabstep",
            "Spok co do kurwy",
            "Nie no spoko komputer do przepraszania",
        ]
        self.chats = []

    def update(self):
        self.url_path_to_schedule = "http://www.sci.edu.pl/plan/plany/o12.html"
        self.hours = self.downloadHoursFromWeb()
        self.time_table = self.downloadTimetableFromWeb()

    def downloadHoursFromWeb(self):
        godziny = []

        page = urllib2.urlopen(self.url_path_to_schedule)
        soup = BeautifulSoup(page.read(), "html.parser")
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

    def downloadTimetableFromWeb(self):
        """
        Metoda pobiera plan/lekcje ze strony planu i zwraca w postaci listy
        :return:[list]lekcje
        """
        page = urllib2.urlopen(self.url_path_to_schedule)
        return self.parseTimetableFromHTML(page)


    def parseTimetableFromHTML(self, html):
        timetable = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]     #TODO znalezc inne rozwiazanie
        soup = BeautifulSoup(html.read(), "html.parser")
        hour = 0
        table_rows=soup.findAll('tr')

        for table_row in table_rows:
            day = 0
            table_row=table_row.findAll('td',{'class':'l'})
            for lesson in table_row:
                classroom = lesson.findAll('a', {'class':'s'})
                lesson = lesson.findAll('span', {'class':'p'})
                if(len(lesson)==0):
                    timetable[hour].append("")
                for subject in lesson:
                    if(len(classroom)==0):
                        timetable[hour].append(subject.string)
                    else:
                        timetable[hour].append(subject.string + " " + classroom[0].string)
                day += 1
            hour += 1

        logging.info(json.loads(json.dumps(timetable)))
        timetable = timetable[3:]
        return timetable

    def getTimetableForDayAsString(self, day):
        if day > 4:
            day = 0

        result = ""
        index = 0

        for i in range(0,9):
            lekcja = self.time_table[i][day]
            result += self.hours[index][0] + "-" + self.hours[index][1] + ": " + lekcja + "\r\n"

            # To kod w przypadku gdy beda okienka w planie
            """
            if len(lekcja)>0:
                wynik += self.godziny[index][0] + "-" + self.godziny[index][1] + ": " + lekcja + "\r\n"
            elif i>3:
                if len(self.lekcje[i-1][numer])>0:
                    wynik += self.godziny[index][0] + "-" + self.godziny[index][1] + ": " + lekcja + "\r\n"
            """

            index += 1
        return result

    def getLessonForDayAndHour(self, day, hour_index):
        # Zapobiega odwolywania sie do nieistniejacego indexu
        if day > 4:
            day = 0

        # Zapobiega odwolywania sie do nieistniejacego indexu
        # Nie mamy w planie danych dla godziny wiecej niz 10tej
        if hour_index > 8:
            hour_index = 0

        return self.time_table[hour_index][day]

    def getNextLesson(self):
        date = datetime.datetime.now()
        hour_now = date.hour + 1
        minute_now = date.minute
        day_now = date.weekday()

        # Zapobiega odwolywania sie do nieistniejacego indexu
        if day_now > 4:
            day_now = 0

        for i in range(len(self.hours)):
            lesson_start_time = self.hours[i][0]
            lesson_hour_start = int(lesson_start_time[:lesson_start_time.find(":")])
            lesson_minute_start = int(lesson_start_time[lesson_start_time.find(":")+1:])

            if (hour_now < lesson_hour_start) or (hour_now == lesson_hour_start and minute_now <= lesson_minute_start):
                next_lesson = self.getLessonForDayAndHour(day_now, i)
                if len(next_lesson)>0:
                    return self.hours[i][0] + " - " + self.hours[i][1] + " " + next_lesson

        # Jeszcze raz tym razem bez sprawdzania godziny
        # Zwracamy pierwsza lekcje nastepnego dnia
        for i in range(len(self.hours)):
            next_lesson = self.getLessonForDayAndHour(day_now+1, i)
            if len(next_lesson)>0:
                return self.hours[i][0] + " - " + self.hours[i][1] + " " + next_lesson

        return "Jak ty to zrobiles?"