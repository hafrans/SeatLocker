import multiprocessing
import threading
import sqlite3
import logging
import time
import os
import sys

sys.path.append("..")

from sqlite3 import Row
from datetime import datetime
from threading import Thread
from seat.__future__ import *
from .error import *
from .premium import PREMIUM_CHECKIN_AUTO
from queue import Queue as TQueue
from multiprocessing.managers import SyncManager
from multiprocessing import Manager, Process, Pool, Lock, Queue

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s")


resultQueue = TQueue()


SQL_ALL_PERSON = """
                select
                    u.id as id,
                    u.username as username,
                    u.password as password,
                    u.register_time as register_time,
                    u.priority as priority,
                    u.school as school,
                    s.email as email,
                    s.phone as phone ,
                    s.checkin as checkin,
                    s.reserve as reserve,
                    s.auto_checkin as auto_checkin,
                    s.random_reserve as random_reserve
                from users as u inner join settings as s on s.user = u.id where s.auto_checkin > 0 or s.auto_checkin = -1
                """


def remoteExecute(sqlstr,args):
    target = {
        'sql':sqlstr,
        'args':args
    }
    resultQueue.put(target)
    pass

def sqlThreadWorker():
    logging.info("已加载SQL THREAD WORKER"+threading.current_thread().getName())
    initdb = sqlite3.connect("data/sqlite.db")
    initdb.row_factory = sqlite3.Row
    commit_counter = 0
    while True:
        try:
            cursor = initdb.cursor()
            info = resultQueue.get()
            cursor.execute(info['sql'],info['args'])
            commit_counter = (commit_counter + 1) % 100
        except Exception as e:
            logging.error(e)
        finally:
            if commit_counter % 5 == 0 or resultQueue.empty():
                logging.info("SQL THREAD WORK 已经执行一次提交"+threading.current_thread().getName())
                initdb.commit()
            cursor.close()
    else:
        initdb.close()

def loggme(x):
    logging.info(x)

def deploy(duration=15,processNumber=None):
    deployQueue = Manager().Queue(30)
    if processNumber == None:
        processNumber = os.cpu_count()
        if processNumber == None:
            processNumber = 1
    logging.info("use {0} processes".format(processNumber))
    server = SyncManager(address=('127.0.0.1',56131),authkey=b'13056')
    server.register("result",callable=remoteExecute)
    server.register("logging",callable=loggme)
    # server.register("queue",callable=deployQueue)
    #deploy the thread workers
    sqlthread = Thread(target=sqlThreadWorker,name="sql Thread worker")
    sqlthread.daemon = True
    sqlthread.start()
    userthread = Thread(target=getAllUserWorker,args=(deployQueue,duration,))
    userthread.daemon = True
    userthread.start()
    """
       for multiprocess
    """
    _pool = Pool()

    for i in range(processNumber):
        _pool.apply_async(doWork,(deployQueue,))
        logging.info("已部署第{0}个进程".format(i+1))
    server.get_server().serve_forever()


def doWork(q):
    try:
        time.sleep(1)
        server = SyncManager(address=('127.0.0.1',56131),authkey=b'13056')
        server.connect()
        server.logging("远程服务器连接成功！")
        obj = None
        while True:
            info = q.get()
            server.logging(info)
            try:
                if CAMPUS_CHECKIN_ENABLED(CAMPUS(info['school'],info['auto_checkin'])):
                    targetAmount = info['checkin']
                    if targetAmount == -1:
                        pass
                    if targetAmount == -2:
                        continue
                    if targetAmount - PREMIUM_CHECKIN_AUTO < 0:#不能低于0 啊否则炸锅了
                        targetAmount = 0
                    else:
                        targetAmount -= 1
                    obj,result = SeatClient.quickCheckin(info['school'],info['auto_checkin'],info['username'],info['password'],info['id'],obj)
                    if result:
                        print("执行成功！")
                        server.result("insert into log (user,time,jigann,content,type) values(?,?,?,?,?)",(info['id'],datetime.today.__str__(),"[{0},{1}]签到成功".format(info['username'],info['school']),10,))
                        server.result("update settings set checkin = ? where user = ?",(targetAmount,info['id']))
            except SeatReservationException as e:
                #failed
                server.result("insert into log (user,time,jigann,content,type) values(?,?,?,?,?)",(info['id'],datetime.today.__str__(),"[{0},{1}]签到失败，错误码{2}".format(info['username'],info['school'],e.type),LOG_STATUS_CHECKIN))
            except Exception as e:
                server.result("insert into log (user,time,jigann,content,type) values(?,?,?,?,?)",(info['id'],datetime.today.__str__(),"[{0},{1}]签到错误，错误码{2}".format(info['username'],info['school'],e),LOG_ERR_CHECKIN))
                server.logging(e)
    except Exception as e:
        print(e)
    finally:
        pass

    pass


def getAllUserWorker(deployQueue,duration = 15):
    """
        获取所有学生的信息，注入queue
    """
    logging.info("已加载GET ALL USER WORKER"+threading.current_thread().getName())
    initdb = sqlite3.connect("data/sqlite.db") 
    initdb.row_factory = sqlite3.Row
    while True:
        try:
            cursor = initdb.cursor()
            for i in cursor.execute(SQL_ALL_PERSON):
                deployQueue.put(dict(i))
            time.sleep(duration)
        except Exception as err:
            logging.error(err)
        finally:
            cursor.close()
            time.sleep(10)
    initdb.close()

if __name__ == "__main__":
    multiprocessing.freeze_support() 
    deploy()