from google.appengine.ext import db
import datetime
import logging
import utils
import webapp2
from collections import Counter
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

def putLogRow(chat_id, user_id, username, chatname, date, msg):
    text = db.Text(msg)
    logging.info("Logging message")
    e = LogRow(chat_id=chat_id, user_id=user_id, username=username, chatname=chatname, date=date, msg=text)
    e.put()

def getStats(chat_id):
    chat_id = str(chat_id)
    all_rows = db.GqlQuery("SELECT * FROM LogRow WHERE chat_id=:1", chat_id)

    n_array = []
    for row in all_rows:
        n_array.append(row.username)
    c = Counter( n_array )
    logging.info( str(c.items()) )
    return( c.items() )

def getStatsPrevMonth(chat_id):
    chat_id = str(chat_id)
    date = datetime.datetime.now() - datetime.timedelta(seconds=60)
    date = date.strftime('%Y-%m-%d %H:%M:%S')
    all_rows = db.GqlQuery("SELECT * FROM LogRow WHERE chat_id=:1 AND date > DATETIME(:2)", chat_id, date)
    n_array = []
    for row in all_rows:
        n_array.append(row.username)
    c = Counter( n_array )
    logging.info( str(c.items()) )
    return( c.items() )