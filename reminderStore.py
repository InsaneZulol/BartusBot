from google.appengine.ext import db
import datetime
import logging
import utils
import webapp2
from collections import Counter
import main
from datetime import timedelta

class ReminderRow(db.Model):
    chat_id = db.StringProperty()
    date_income = db.DateTimeProperty(auto_now_add=True)
    date = db.DateTimeProperty()
    msg = db.StringProperty()
    msg_id = db.StringProperty()

def putReminderRow(_chat_id, _date_income, _date, _msg, _msg_id):
    logging.info("Adding row")
    e = ReminderRow(chat_id=_chat_id, date_income=_date_income, date=_date, msg=_msg, msg_id=_msg_id)
    e.put()

def getExpiredRows():
    date = datetime.datetime.now()
    logging.info("reminderStore: " + "DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    expired_rows = db.GqlQuery("SELECT * FROM ReminderRow WHERE date < DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    try:
        logging.info("expired count:" + str(len(expired_rows)))
    except:
        logging.info("zero expired")

    return expired_rows

def getAllRows():
    all_rows = db.GqlQuery("SELECT * FROM ReminderRow")
    return all_rows

def deleteReminds(expired_rows):
    for row in expired_rows:
        logging.info("Usuwanie")
        db.delete(row)

def deleteRemind(row):
    logging.info("Usuwanie")
    db.delete(row)


class LogRow(db.Model):
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    username = db.StringProperty()
    chatname = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    msg = db.TextProperty()

class MessageCounter(db.Model):
    chat_id = db.StringProperty()
    user_id = db.StringProperty()
    username = db.StringProperty()
    count = db.IntegerProperty()

def putLogRow(chat_id, user_id, username, chatname, date, msg):
    text = db.Text(msg)
    logging.info("Logging message")
    e = LogRow(chat_id=chat_id, user_id=user_id, username=username, chatname=chatname, date=date, msg=text)
    q = MessageCounter.all()
    q.filter('chat_id =', chat_id).filter('user_id =', user_id)
    counter = q.get()
    #counter = db.GqlQuery("SELECT * FROM MessageCounter WHERE chat_id=:1 AND user_id=:2", (chat_id,user_id))
    if not counter:
        counter = MessageCounter(chat_id = chat_id, user_id = user_id, username=username, count = 1)
    else:
        logging.info("UWAGA COUNTER TO: "+ str(counter.count))
        counter.count += 1
    e.put()
    counter.put()

def getStats(chat_id):
    # chat_id = str(chat_id)
    # all_rows = db.GqlQuery("SELECT * FROM LogRow WHERE chat_id=:1", chat_id)
    #
    # n_array = []
    # for row in all_rows:
    #     n_array.append(row.user_id)
    # c = Counter( n_array )
    # logging.info( str(c.items()) )
    # sorted_array = sorted(c.items(), key=lambda user: user[1], reverse=True)
    # logging.info(sorted_array)
    # #return( c.items() )
    # return( sorted_array )
    chat_id = str(chat_id)
    q = MessageCounter.all()
    q.filter('chat_id =', chat_id)
    #message_counters = q.get()
    wynik = []
    for row in q.run():
        wynik.append((row.username, row.count))
    return wynik

def getStatsPrevMonth(chat_id):
    chat_id = str(chat_id)
    date = datetime.datetime.now() - datetime.timedelta(seconds=60)
    all_rows = db.GqlQuery("SELECT * FROM LogRow WHERE chat_id=:1", chat_id)
    #all_rows = db.GqlQuery("SELECT * FROM LogRow WHERE chat_id='"+chat_id+"' AND date > DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    n_array = []
    for row in all_rows:
        n_array.append(row.username)
    c = Counter( n_array )
    logging.info( str(c.items()) )
    return( c.items() )

def getNameFromId(id):
    q = MessageCounter.all()
    q.filter('user_id =', id)
    user = q.get()
    return user.username
    # if id in main.USERNAMES:
    #     return main.USERNAMES[str(id)]
    # else:
    #     return str(id)
    #     # id = str(id)
    #     # name = str(id)
    #     # query = db.GqlQuery("SELECT * FROM LogRow WHERE user_id=:1 LIMIT 1", id)
    #     # for row in query:
    #     #     return row.username
    #     # return str(id)
