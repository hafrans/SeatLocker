import multiprocessing
import threading
import sqlite3
import logging
import time
import os
import sys

sys.path.append("..")

from .error import *
from sqlite3 import Row
from datetime import datetime
from threading import Thread
from seat.__future__ import *
from queue import Queue as TQueue
from multiprocessing.dummy import Pool as TPool
from .premium import PREMIUM_CHECKIN_AUTO
from multiprocessing.managers import SyncManager
from .utils import getServerTimePRC, parseDateWithTz
from multiprocessing import Manager, Process, Pool, Lock, Queue

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s")


resultQueue = TQueue()
# localresultQueue = TQueue()


"""
    获取开启抢座的而且有使用点数的
"""
SQL_ALL_AUTOCHECKIN_PERSON = """
                select
                    u.id as id,
                    u.username as username,
                    u.password as password,
                    u.token as token,
                    u.register_time as register_time,
                    u.priority as priority,
                    u.school as school,
                    s.email as email,
                    s.phone as phone ,
                    s.checkin as checkin,
                    s.reserve as reserve,
                    s.auto_checkin as auto_checkin,
                    s.random_reserve as random_reserve
                from users as u inner join settings as s on s.user = u.id where s.auto_checkin > 0 and s.checkin > -2
                """

"""
    获取时间段内(julianday('now') > julianday(start_date)  or ( end_date is null and julianday('now') < julianday(end_date)) )
    并且剩余reserve点数大于-1，而且开启自动抢座
"""
SQL_ALL_RESERVATION_PERSON = """
    select 
          users.id as id,
          seat.user as user ,
          users.username as username,
          users.password as password,
          users.school as school
    from 
          seat 
    inner join
          settings
    on
          seat.user = settings.user
    inner join
          users
    on    seat.user = users.id and settings.user = users.id
    where  (
                julianday('now') > julianday(seat.start_date)  
                 or  (seat.end_date is null and julianday('now') < julianday(seat.end_date))
            ) 
          and settings.reserve != -2 and settings.auto_reserve = 1 
    group by seat.user
"""
SQL_ALL_RESERVATION_SEATS = """
                select
                    s.email as email,
                    s.phone as phone ,
                    s.reserve as reserve,
                    s.random_reserve as random_reserve,
                    s.auto_reserve as auto_reserve,
                    e.user as user,
                    e.room as room,
                    e.seat as seat,
                    e.name as name,
                    e.start_time as start_time,
                    e.end_time as end_time,
                    e.start_date as start_date,
                    e.end_date as end_date,
                    e.priority as priority,
                    e.tuesday as tuesday
                from settings as s inner join seat as e on s.user = e.user
                where (julianday('now') >= julianday(e.start_date)  or ( e.end_date is null and julianday('now') < julianday(e.end_date)) ) and s.reserve != -2 and s.auto_reserve = 1 and e.user = ? order by e.priority desc, e.id asc

"""
##################################################################################
# 远程执行SQL
def remoteExecute(sqlstr,args):
    """
        An interface of remote sql executor.
    """
    target = {
        'sql':sqlstr,
        'args':args
    }
    resultQueue.put(target)
    pass

def sqlThreadWorker():
    """
        Automatic sql executor using a Thread Queue.
    """
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
            logging.debug(info)
        except Exception as e:
            logging.error(e)
        finally:
            if commit_counter % 5 == 0 or resultQueue.empty():
                logging.info("SQL THREAD WORK 已经执行一次提交"+threading.current_thread().getName())
                initdb.commit()
            cursor.close()
    initdb.close()

def loggme(x):
    logging.info(x)

###########################################################################################
# Main Deploy.
def deploy(duration=15,processNumber=None):
    checkinQueue = Manager().Queue(30) #自动位置签到
    reserveQueue = Manager().Queue()   #自动抢座
    #分布式服务器（加锁）
    server = SyncManager(address=('0.0.0.0',56131),authkey=b'13056')
    server.register("result",callable=remoteExecute)
    server.register("logging",callable=loggme)
    server.register("checkin_queue",callable=lambda : checkinQueue)
    server.register("reserve_queue",callable=lambda : reserveQueue)

    #deploy the thread workers
    sqlthread = Thread(target=sqlThreadWorker,name="sql Thread worker")
    sqlthread.daemon = True
    sqlthread.start()

    # depoly checkin user fetch worker. #队列线程
    userthread = Thread(target=getAllCheckinUserWorker,args=(checkinQueue,duration,))
    userthread.daemon = True
    userthread.start()

    #deploy auto reservation fetch worker; #队列线程
    userthread_reserve = Thread(target=getAllAutoReservationUserWorker,args=(reserveQueue,))
    userthread_reserve.daemon = True
    userthread_reserve.start()


    #spawnProcess #本地进程
    spawnProcess(processNumber)

    logging.info("***分布式协作接口开启***")
    logging.info("***Distributed Cooperating Interface is Deployed.*** ")
    import gc  
    # import objgraph  
    # ### 强制进行垃圾回收  
    # gc.collect()  
    # ### 打印出对象数目最多的 50 个类型信息  
    # objgraph.show_most_common_types(limit=50)  
    server.get_server().serve_forever()

def spawnProcess(processNumber):
    """
       for multiprocess
    """
    if processNumber == None:
        processNumber = os.cpu_count()
        if processNumber == None:
            processNumber = 1
    logging.info("use {0} processes".format(processNumber))
    _pool = Pool(processes = processNumber) #进程池
    _fin_n = 2 if processNumber <= 2 else processNumber
    for i in range(_fin_n):
        _pool.apply_async(doAutoCheckinWork)
        _pool.apply_async(doAutoReserveWork)
    logging.info("进程部署完毕")
    return _pool
    

def clientDeploy(processNumber = None):
    """
        A method like deploy. But it runs in client role.
        just spawns processes and runs local proxy for remote execution
        do not run client and server role at the same time!
    """
    """
       for multiprocess
    """
    return spawnProcess(processNumber)

def doAutoCheckinWork():
    try:
        time.sleep(1)
        server = SyncManager(address=('127.0.0.1',56131),authkey=b'13056')
        server.connect()
        server.logging("*** 有外部Work接入啦！")
        obj = None
        while True:
            _queue = server.checkin_queue()
            info = _queue.get()
            server.logging(str(dict(info))+ "=========" + str(os.getpid()))
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
                    obj,result = SeatClient.quickCheckin(info['school'],info['auto_checkin'],info['username'],info['password'],info['id'],info['token'],obj)
                    if result:
                        localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到成功".format(info['username'],info['school']),10,))
                        localExecuteProxy(server,"update settings set checkin = ? where user = ?",(targetAmount,info['id']))
            except SeatReservationException as e:
                #failed
                if e == SeatReservationException.NO_AVAILABLE_RESERVATIONS or e == SeatReservationException.RESERVE_HAVE_CHECKEDIN:
                    pass
                else:
                    localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到失败，{2}".format(info['username'],info['school'],e.message),LOG_STATUS_CHECKIN))
               
            except Exception as e:
                localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到错误，{2}".format(info['username'],info['school'],e),LOG_ERR_CHECKIN))
                server.logging(e)
    except Exception as e:
        print(e)
    finally:
        pass

def doAutoReserveWork():
    """
        执行占座任务 4点55登录，4.58开始预约
    """
    ##使用协程gevent 库 废弃，对这个不友好！
    # import gevent
    # from gevent import monkey
    # # monkey.patch_socket()
    # monkey.patch_builtins()
    # monkey.patch_time()
    logging.info("自动约座进程{0}已开启..".format(str(os.getpid())))
    time.sleep(1)#wait for server.
    retry_threshold = 500 #最大错误阈值
    ######
    # 时间控制
    #####
    stage_1_time = datetime.today().replace(hour=4,minute=55,second=0) #登录时间
    stage_2_time = datetime.today().replace(hour=4,minute=59,second=58) #抢座时间
    try:
        #连接分布式服务器。
        server = SyncManager(address=('127.0.0.1',56131),authkey=b'13056')
        server.connect()
        server.logging("***已加载一个分布式自动约座组件进程***"+str(os.getpid()))
    except Exception as e:
        print(e)
    reserveQueue = server.reserve_queue()
    def process(userBody):
        #每人一个小线程，时间耗在IO。
        #肯定len >= 1否则数据库查不出来
        user = userBody['user'] # 用户信息
        seats = userBody['seats'] # 用户位置
        retry = 0
        person = None
        statusOk = False
        #开始第一阶段
        print("***{0} process 开始第一阶段！***".format(user['username']))
        delta = parseDateWithTz(stage_1_time) - getServerTimePRC(SCHOOL(user['school'])['BASE']) #第一阶段时间减去服务器时间。
        print("正在等待至第一阶段进行登录,"+str(delta.days * 86400 + delta.seconds)+"秒...")
        time.sleep(delta.days * 86400 + delta.seconds if delta.days * 86400 + delta.seconds > 0 else 0)
        while True:
            try:
                person = SeatClient.NewClient(user['username'],user['password'],campus=CAMPUS(user['school']),school=user['school'])
                break
            except UserCredentialError as e:
                logToRemote(server,user,"自动预约失败,登陆异常({0})".format(e),LOG_STATUS_RESERVATION)
                return
            except Exception as e:
                logToRemote(server,user,"自动预约失败,其他错误({0})".format(e),LOG_DEBUG_RESERVATION)
                continue
            finally:
                retry += 1
                if retry >= 10:
                    logToRemote(server,user,"自动预约失败,错误次数超出阈值",LOG_ERR_RESERVATION)  
                if statusOk:
                    return
        
        #登录成功后休息
        #等待抢座
        delta = (parseDateWithTz(stage_2_time) - getServerTimePRC(SCHOOL(user['school'])['BASE'])) #第二阶段时间减去服务器时间。
        print("正在等待至第二阶段进行登录,"+str(delta.days * 86400 + delta.seconds)+"秒...")
        time.sleep(delta.days * 86400 + delta.seconds if delta.days * 86400 + delta.seconds > 0 else 0)
        person.login() #强制重新登录
        #开始抢座
        while True:
            try:
                for seat in seats: #座位候选
                    timelimit = 0
                    while not statusOk:
                        try:
                            #默认是第二天的
                            person.reserveSeat(seat['seat'],startTime=seat['start_time'],endTime=seat['end_time'],layoutDate=None,tuesdayType= True if seat['tuesday'] == 1 else False)
                            statusOk = True
                            logToRemote(server,user,"已成功预约,{0}".format(seat['name']),LOG_OK_RESERVATION)
                        except SeatReservationException as err:
                            if err == SeatReservationException.FAILED_RESERVED:#位置被抢
                                break #赶快进行下一个
                            elif err == SeatReservationException.HAVE_RESERVED:# 有重复预约
                                logToRemote(server,user,"当日已经存在一个预约，不可重复预约！",LOG_STATUS_RESERVATION)
                                return #退出进程
                            elif err == SeatReservationException.NOT_IN_RESERVE_TIME: 
                                if timelimit > 1:
                                    time.sleep(0.9)
                                else:
                                    time.sleep(timelimit)
                                    timelimit += 0.1
                                continue
                            elif err == SeatReservationException.TIME_SPAN_ERROR:
                                logToRemote(server,user,"座位预约时段不正确！",LOG_STATUS_RESERVATION)
                                break
                            elif err == SeatReservationException.LICENSE_EXPIRED:
                                logToRemote(server,user,"图书馆许可证过期",LOG_STATUS_RESERVATION)
                                return
                            else:
                                logToRemote(server,user,"其他错误({0})".format(err.type),LOG_STATUS_RESERVATION)
                        except Exception as err:
                            #可能是网络等问题
                            if "参数错误" in str(err):
                                 logToRemote(server,user,"自动预约失败,{0}".format(str(err)),LOG_DEBUG_RESERVATION)
                                 print("退出")
                                 return
                            logToRemote(server,user,"自动预约失败,{0}".format(str(err)),LOG_DEBUG_RESERVATION)
                            time.sleep(0.1)
                            continue
                        finally:
                            retry += 1
                            if retry >= retry_threshold:
                                logToRemote(server,user,"自动预约失败,错误次数超出阈值",LOG_STATUS_RESERVATION)
                                return  
                            if statusOk:
                                break
                    #这次while执行完毕后检查还需要找下一位？
                    if statusOk:
                        break #跳出for
                    else:
                        if timelimit > 1:
                            time.sleep(0.9)
                        else:
                            time.sleep(timelimit)
                            timelimit += 0.1
                else: #for最终处理
                    logToRemote(server,user,"自动预约失败,全部候选座位预约失败",LOG_STATUS_RESERVATION)
                    statusOk = True
                #end for
                    
                
            except UserCredentialError as err:
                #登录之类的事情都在这里
                print("ERROR"+str(err))
                logToRemote(server,user,"自动预约失败,登陆异常({0})".format(err.type),LOG_ERR_RESERVATION)
                return
            finally:
                retry += 1
                if retry >= retry_threshold:
                    logToRemote(server,user,"自动预约失败,错误次数超出阈值",LOG_ERR_RESERVATION)  
                    return 
                if statusOk:
                    return
    pass  
    _t_poll = TPool()
    try:
        while True:
            body = reserveQueue.get()
            _t_poll.apply_async(process,(body,))
            time.sleep(0.5)
    except Exception as e:
        print(e)
       

            
    

def getAllCheckinUserWorker(deployQueue,duration = 30):
    """
        获取所有学生的信息，注入queue
    """
    logging.info("已加载获取自动签到子进程 GET ALL USER CHECKIN WORKER"+threading.current_thread().getName())
    time.sleep(10) # 等10秒
    initdb = sqlite3.connect("data/sqlite.db") 
    initdb.row_factory = sqlite3.Row
    while True:
        if datetime.today().hour > 22 or datetime.today() < datetime.today().replace(hour=6,minute=45):
            time.sleep(60)
            continue
        logging.info(threading.current_thread().getName()+"执行一次用户抓取用于签到")
        try:
            cursor = initdb.cursor()
            for i in cursor.execute(SQL_ALL_AUTOCHECKIN_PERSON):
                deployQueue.put(dict(i))
            time.sleep(duration*60)
        except Exception as err:
            logging.error(err)
        finally:
            cursor.close()
            time.sleep(10)
    initdb.close()

def getAllAutoReservationUserWorker(deployQueue):
    """
      获取所有 在4点半开始执行。
    """
    logging.info("已加载自动约座。GET ALL USER RESERVATION WORKER"+threading.current_thread().getName())
    initdb = sqlite3.connect("data/sqlite.db") 
    initdb.row_factory = sqlite3.Row
    logging.info("正在等待数据投放时间（4.30）"+threading.current_thread().getName())
    while True: # 每天一个循环。
        try:
            if datetime.today().hour == 4 and datetime.today().minute == 30:
                logging.info("启动一次用户约座部署器。GET ALL USER RESERVATION WORKER"+threading.current_thread().getName())
            else:
                time.sleep(30)
                continue

            cursor = initdb.cursor()
            #获取开通自动占座的用户，
            for i in cursor.execute(SQL_ALL_RESERVATION_PERSON):
                _resultBundle = [dict(x) for x in cursor.execute(SQL_ALL_RESERVATION_SEATS,(i['user'],)).fetchall() ] 
                # logging.info(str(_resultBundle)+threading.current_thread().getName())
                deployQueue.put({'seats':_resultBundle,'user':dict(i)})
            cursor.close()
            time.sleep(86000)
        except Exception as err:
            logging.error(err)
        finally:
            time.sleep(10)
    initdb.close()

#####################################################
# 本地 log 使用本地队列RPC到远端入库
def logToRemote(server,userinfo,content,typz = 0):
    """
     向远程写数据库，
    """
    localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(userinfo['id'],datetime.today().__str__(),"[{0},{1}]{2}".format(userinfo['username'],userinfo['school'],content),typz))
    

def localExecuteProxy(server,sqlstr,args):
    """
        待优化
    """
    server.result(sqlstr,args)

