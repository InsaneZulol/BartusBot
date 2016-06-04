from google.appengine.ext import db
import datetime
import logging
import schedule
import webapp2
from collections import Counter
import main
from datetime import timedelta

class ReminderRow(db.Model):
    """
    Tabela w Datastore do przechowywania przypomnien
    """
    chat_id = db.StringProperty()
    date_income = db.DateTimeProperty(auto_now_add=True)
    date = db.DateTimeProperty()
    msg = db.StringProperty()
    msg_id = db.StringProperty()

def putReminderRow(_chat_id, _date_income, _date, _msg, _msg_id):
    """
    Metoda dodajaca przypomnienie do bazy
    :param _chat_id:
    :param _date_income:
    :param _date:
    :param _msg:
    :param _msg_id:
    :return:
    """
    logging.info("Adding row")
    e = ReminderRow(chat_id=_chat_id, date_income=_date_income, date=_date, msg=_msg, msg_id=_msg_id)
    e.put()

def getExpiredRows():
    """
    Metoda zwracajaca przeterminowane, wygasle przypomnienia, czyli te ktore nalezy wyslac
    :return:
    """
    date = datetime.datetime.now()
    logging.info("reminderStore: " + "DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    expired_rows = db.GqlQuery("SELECT * FROM ReminderRow WHERE date < DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    try:
        logging.info("expired count:" + str(len(expired_rows)))
    except:
        logging.info("zero expired")

    return expired_rows

def getAllRows():
    """
    Zwraca wszystkie przypomnienia
    :return:
    """
    all_rows = db.GqlQuery("SELECT * FROM ReminderRow")
    return all_rows

def deleteReminds(expired_rows):
    """
    Usuwa podane przypomnienia
    :param expired_rows:
    :return:
    """
    for row in expired_rows:
        logging.info("Usuwanie")
        db.delete(row)

def deleteRemind(row):
    """
    Usuwa pojedyncze przypomnienie
    :param row:
    :return:
    """
    logging.info("Usuwanie")
    db.delete(row)


class LogRow(db.Model):
    """
    Tabela z logami wiadomosci
    """
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    username = db.StringProperty()
    chatname = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    msg = db.TextProperty()

class MessageCounter(db.Model):
    """
    Tabela ze statystykami
    """
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    username = db.StringProperty()
    count = db.IntegerProperty()

class NicknamesInChats(db.Model):
    """
    Tabela ze statystykami
    """
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    nickname = db.StringProperty()

class WeekMessageCounter(db.Model):
    """
    Tabela z tygodniowymi statystykami
    """
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    username = db.StringProperty()
    count = db.IntegerProperty()

def putLogRow(chat_id, user_id, username, chatname, date, msg, nickname):
    """
    Dodawanie wiadomosci do tabeli z logami
    :param chat_id:
    :param user_id:
    :param username:
    :param chatname:
    :param date:
    :param msg:
    :return:
    """
    text = db.Text(msg)
    logging.info("Logging message")
    e = LogRow(chat_id=chat_id, user_id=user_id, username=username, chatname=chatname, date=date, msg=text)

    # Statystyki wiadomosci
    q = MessageCounter.all()
    q.filter('chat_id =', chat_id).filter('user_id =', user_id)
    counter = q.get()
    #counter = db.GqlQuery("SELECT * FROM MessageCounter WHERE chat_id=:1 AND user_id=:2", (chat_id,user_id))
    if not counter:
        counter = MessageCounter(chat_id = chat_id, user_id = user_id, username=username, count = 1)
    else:
        logging.info("UWAGA COUNTER TO: "+ str(counter.count))
        counter.count += 1

    # Do listy uzytkownikow chatu
    if nickname != "":
        n = NicknamesInChats.all()
        n.filter('chat_id =', chat_id).filter('user_id =', user_id)
        nickname_o = n.get()
        if not nickname_o:
            nickname_o = NicknamesInChats(chat_id=chat_id, user_id=user_id, nickname=nickname)
        nickname_o.put()

    w_q = WeekMessageCounter.all()
    w_q.filter('chat_id =', chat_id).filter('user_id =', user_id)
    w_counter = w_q.get()
    if not w_counter:
        w_counter = WeekMessageCounter(chat_id = chat_id, user_id = user_id, username=username, count = 1)
    else:
        w_counter.count += 1

    e.put()
    counter.put()
    w_counter.put()

def getNicknames(chat_id):
    chat_id = str(chat_id)
    q = NicknamesInChats.all()
    q.filter('chat_id =', chat_id)
    wynik = []
    for row in q.run():
        wynik.append(row.nickname)
    return wynik

def getStats(chat_id):
    """
    Pobieranie statystyk
    :param chat_id:
    :return:
    """
    chat_id = str(chat_id)
    q = MessageCounter.all()
    q.filter('chat_id =', chat_id)
    #message_counters = q.get()
    wynik = []
    for row in q.run():
        wynik.append((row.username, row.count))
    wynik.sort(key=lambda x: x[1], reverse=True)
    return wynik

def getWeekStats(chat_id):
    """
    Pobieranie tygodniowych statystyk
    :param chat_id:
    :return:
    """
    chat_id = str(chat_id)
    q = WeekMessageCounter.all()
    q.filter('chat_id =', chat_id)
    #message_counters = q.get()
    wynik = []
    for row in q.run():
        wynik.append((row.username, row.count))
    wynik.sort(key=lambda x: x[1], reverse=True)
    return wynik

def resetWeekStats():
    """
    Resetowanie tygodniowych staystyk
    :return:
    """
    all_rows = db.GqlQuery("SELECT * FROM WeekMessageCounter")
    for row in all_rows:
        logging.info("Resetowanie tygodniowych statystyl")
        db.delete(row)

def getNameFromId(id):
    """
    Pobieranie nazwy dla danego user_id
    :param id:
    :return:
    """
    q = MessageCounter.all()
    q.filter('user_id =', id)
    user = q.get()
    return user.username
