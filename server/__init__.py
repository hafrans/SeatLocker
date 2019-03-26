
import sys
import os
sys.path.append("..")

from seat.__future__ import *
from flask import Flask
import flask_restful
from flask_restful import Resource, Api
from .user import *
from flask import session
from flask_restful import abort
import sqlite3
from sqlite3 import Row
from flask import g

__all__ = ['app']

app = Flask(__name__)
api = Api(app)



app.secret_key = os.urandom(24)
DATABASE = "./data/sqlite.db"
DATABASE_INIT_FILE = "./data/init.sql"


##################################
#  Database Initialization
##################################
init_flag = False
app.logger.debug("--------database------initializtion------------------")
if not os.path.exists(DATABASE):
    # initialize now
    app.logger.info("I will initialize a new database!")
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
            app.logger.debug("database is initialized.")
        except Exception as e:
            print(e)
            app.logger.debug("database initialization failed.")
            init_flag = True
else:
    app.logger.debug("DataBase have initialized.")

app.logger.debug("--------database------initializtion------------------")
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




@app.teardown_request
def teardown_request(exception):
    closeDatabase()


################################

def custom_error(http_status_code, *args, **kwargs):
    if http_status_code == 400:
        abort(400,**{'code':'12','message':'参数错误','fields':kwargs.get('message',None)})
    abort(http_status_code,**kwargs)


flask_restful.abort = custom_error

api.add_resource(User,"/",endpoint="user")


