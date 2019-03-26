
import sqlite3

def returnData(code,status,message,kwargs):
    return {'code':code,'status':status,'message':message,'data':kwargs} ,200

def parseDate(date):
    return date.replace(microsecond=0)