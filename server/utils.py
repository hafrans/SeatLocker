
import sqlite3

headers = {
    "Access-Control-Allow-Headers":"X-Requested-With, accept, content-type, *",
    "Access-Control-Allow-Origin":"*",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods":"GET, HEAD, POST, PUT, DELETE, TRACE, PATCH"
}


def returnData(code,status,message,kwargs):
    return {'code':code,'status':status,'message':message,'data':kwargs} ,200,headers

def parseDate(date):
    return date.replace(microsecond=0)

def invalidate(session):
    session['entity'] = None