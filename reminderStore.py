from google.appengine.ext import db
import datetime
import logging
import utils
import webapp2
from datetime import timedelta

class ReminderRow(db.Model):
    chat_id = db.StringProperty()
    date_income = db.DateTimeProperty(auto_now_add=True)
    date = db.DateTimeProperty()
    msg = db.StringProperty()

def putReminderRow(_chat_id, _date_income, _date, _msg):
    e = ReminderRow(chat_id=_chat_id, date_income=_date_income, date=_date, msg=_msg)
    e.put()

def getExpiredRows():
    date = datetime.datetime.now() + timedelta(hours=1)
    logging.info("reminderStore: " + "DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    expired_rows = db.GqlQuery("SELECT * FROM ReminderRow WHERE date < DATETIME('"+date.strftime('%Y-%m-%d %H:%M:%S')+"')")
    return expired_rows

def deleteReminds(expired_rows):
    for row in expired_rows:
        db.delete(row)