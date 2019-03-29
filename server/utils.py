
from .error import UserNotLoginError
import os
headers = {
    "Access-Control-Allow-Headers":"X-Requested-With, accept, content-type, *",
    "Access-Control-Allow-Origin":"http://192.168.123.117:8080" ,
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods":"GET, HEAD, POST, PUT, DELETE, TRACE, PATCH"
}
headers["Access-Control-Allow-Origin"] = os.environ.get("APP_HOST",None) or "http://192.168.123.117:8080"



def returnData(code,status,message,kwargs):
    return {'code':code,'status':status,'message':message,'data':kwargs} ,200,headers

def parseDate(date):
    return date.replace(microsecond=0)

def invalidate(session):
    session['entity'] = None

def simpleCheckLogin(session):
    if session.get("entity", None) == None:
        raise UserNotLoginError()