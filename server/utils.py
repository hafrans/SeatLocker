
import os
from .error import UserNotLoginError
from seat.__future__ import SeatClient
import sys
from flask import logging
from datetime import datetime,timezone, timedelta
sys.path.append("..")
import pytz
from urllib import request
from email.utils import parsedate
from .error import TooQuicklyException 
import time


headers = {
    "Access-Control-Allow-Headers": "X-Requested-With, accept, content-type, *",
    "Access-Control-Allow-Origin": "http://192.168.123.117:8080",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, PUT, DELETE, TRACE, PATCH"
}
headers["Access-Control-Allow-Origin"] = os.environ.get("APP_HOST", None) or "http://192.168.123.117:8080"

originAllows = os.environ.get("APP_ORIGIN","").split(";")
logging.logging.info("USE ALLOWED ORIGINs"+os.environ.get("APP_ORIGIN",""))
logging.logging.info("Access-Control-Allow-Origin:"+headers["Access-Control-Allow-Origin"])


SQL_ONE_PERSON = """
                select
                    u.id as id,
                    u.username as username,
                    u.password as password,
                    u.register_time as register_time,
                    u.priority as priority,
                    s.email as email,
                    s.phone as phone ,
                    s.checkin as checkin,
                    s.reserve as reserve,
                    s.auto_checkin as auto_checkin,
                    s.random_reserve as random_reserve
                from users as u inner join settings as s on s.user = u.id where u.id = ?
                """
SQL_STORE_SEAT  = """

    insert into seat (user,room,seat,name,start_time,end_time,start_date,end_date,priority,tuesday,add_date)
    values (?, ?,?,?, ?,?, ?,? ,?,?,?)

"""


## LOG TYPE

LOG_TYPE_CHECK_IN = 101
LOG_TYPE_RESERVE  = 102


def returnData(code, status, message, kwargs):
    return {'code': code, 'status': status, 'message': message, 'data': kwargs}, 200, headers


def parseDate(date):
    return date.replace(microsecond=0)

def parseDateWithTz(date):
    return date.replace(tzinfo=timezone(timedelta(hours=+8)),microsecond=0)


def invalidate(session):
    session['entity'] = None


def simpleCheckLogin(session):
    if session.get("entity", None) == None:
        raise UserNotLoginError()
    return SeatClient.deserialize(session.get('entity'))

def logToDB(g,p,type,content):
    cursor = g.db.cursor()
    cursor.execute("insert into log (user , jigann , content , type )",(p.id,datetime.today().date().__str__(),content,int(type)))
    g.db.commit()
    cursor.close()

def getServerTimePRC(url):
    result = request.urlopen(url)
    rawDatetime = result.headers['Date']
    utctime = parsedate(rawDatetime)
    rawDatetimeObject = datetime(*utctime[:6])
    return rawDatetimeObject.replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone('PRC'))

def freqThreshold(session,key="reqcommon",second = 2):
    res = session.get(key,0)
    if time.time() - res <= second:
        raise TooQuicklyException()
    session[key] = time.time()
