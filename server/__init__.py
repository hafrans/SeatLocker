
import sys
import os
sys.path.append("..")


import flask_restplus
import sqlite3

from seat.__future__ import *
from flask import Flask
from flask import session,abort,g,logging
from flask_restplus import Resource, Api
from flask_compress import Compress
from .basic import *
from .account import *
from .premium import *
from .utils import headers
from .premium import *
from werkzeug.exceptions import HTTPException
from sqlite3 import Row



__all__ = ['app']

app = Flask(__name__)
Compress(app)
api = Api(app,doc=False,)



app.secret_key = os.urandom(24)
DATABASE = "./data/sqlite.db"
DATABASE_INIT_FILE = "./data/init.sql"


##################################
#  Database Initialization
##################################
init_flag = False
logging.logging.debug("--------database------initializtion------------------")
if not os.path.exists(DATABASE):
    # initialize now
    logging.logging.info("I will initialize a new database!")
    os.makedirs(os.path.dirname(DATABASE),exist_ok=True)
    fd = open(DATABASE,mode="wb")
    fd.close()
    with sqlite3.connect(DATABASE) as cx:
        try:
            cu = cx.cursor()
            with open(DATABASE_INIT_FILE,mode="r") as file:
               cu.executescript(file.read().strip())
            cu.close()
            cx.commit()
            logging.logging.debug("database is initialized.")
        except Exception as e:
            print(e)
            logging.logging.debug("database initialization failed.")
            init_flag = True
else:
    logging.logging.debug("DataBase have initialized.")

logging.logging.debug("--------database------initializtion------------------")
##################################
# Database Initialized
##################################
 

def openDatabase():
    if getattr(g,"db",None) == None:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def closeDatabase():
    if getattr(g,"db",None) != None:
        g.db.close()


@app.before_request
def test1():
    openDatabase()

@app.after_request
def apply_caching(response):
    for k,v in headers.items():
        response.headers[k] = v
    return response


@app.teardown_request
def teardown_request(exception):
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    closeDatabase()


################################


##############################
# ADD HANDLERS
##############################

@api.errorhandler(UserCredentialError)
def UserCredentialErrorHandler(err):
    if err == UserCredentialError.TOKEN_EXPIRED:
        invalidate(session)
        return returnData(ERR_LOGIN, 'not login', "令牌失效,请重新登录!", None)
    elif err == UserCredentialError.USER_LOCKED:
        return returnData(ERR_LOGIN, 'not login', err.message,None)
    else:
        return returnData(ERR_LOGIN, 'not login', "用户名或者密码有误",None)

@api.errorhandler(NetWorkException)
def NetWorkExceptionHandler(err):
    invalidate(session)
    return returnData(500,'failed',"目标服务器主机繁忙，请稍后再试",None)

@api.errorhandler(SystemMaintenanceError)
def SystemMaintenanceErrorHandler(err):
    return returnData(501,'failed',"服务器正在维护中，请稍后再试!",None)

@api.errorhandler(UserNotLoginError)
def UserNotLoginErrorHandler(err):
    return returnData(ERR_NOT_LOGIN, 'not login', "用户未登录", None)

@api.errorhandler(SeatNotFoundException)
def SeatNotFoundExceptionHandler(err):
    return returnData(FAILED, 'seat_not_found', "座位不存在", None)

@api.errorhandler(RoomNotFoundException)
def RoomNotFoundExceptionHandler(err):
    return returnData(FAILED, 'not login', "房间不存在", None)

# @api.errorhandler(Exception)
# def ErrorExceptionHandler(err):
#     return returnData(46001,'failed',str(err),None)

# def custom_error(http_status_code, *args, **kwargs):
#     print(http_status_code)
#     if http_status_code == 400:
#         abort(400,**{'code':'12','message':'参数错误','fields':kwargs.get('message',None)})
#     abort(http_status_code,**kwargs)


# flask_restplus.abort = custom_error


api.add_resource(User,"/user","/",endpoint="user")
api.add_resource(Reservation,"/reservation")
api.add_resource(History,"/history")
api.add_resource(Checkin,"/checkin")
api.add_resource(Seats,"/seats/<int:roomId>")
api.add_resource(Room,"/rooms")
api.add_resource(Book,"/book/<date>/<int:roomId>/<int:seatId>/<action>/<int:arg>","/reserveseat")
api.add_resource(AvailableDates,"/dates")
api.add_resource(AutoCheckIn,"/auto/checkin")
api.add_resource(AutoReserve,"/auto/reserve")
api.add_resource(Campus,"/info/campus")
api.add_resource(School,"/info/school")
api.add_resource(GiftCode,"/giftcode")
