
import os
from .error import UserNotLoginError
from seat.__future__ import SeatClient
import sys
from flask import logging
from datetime import datetime
sys.path.append("..")

headers = {
    "Access-Control-Allow-Headers": "X-Requested-With, accept, content-type, *",
    "Access-Control-Allow-Origin": "http://192.168.123.117:8080",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, POST, PUT, DELETE, TRACE, PATCH"
}
headers["Access-Control-Allow-Origin"] = os.environ.get("APP_HOST", None) or "http://192.168.123.117:8080"

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
