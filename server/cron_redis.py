import multiprocessing
import threading
import sqlite3
import logging
import time
import os
import sys
import redis 
import pickle

sys.path.append("..")

from .error import *
from sqlite3 import Row
from datetime import datetime
from threading import Thread
from seat.__future__ import *
from multiprocessing.dummy import Pool as TPool
from .premium import PREMIUM_CHECKIN_AUTO, PREMIUM_RESERVE_AUTO
from .utils import getServerTimePRC, parseDateWithTz
from multiprocessing import Manager, Process, Pool, Lock, Queue
from redis.exceptions import *
from .cron.sqls import *

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s")



def loggingThreadWorker(server):
    logging.info("已加载LOG THREAD WORKER"+threading.current_thread().getName())
    while True:
        s = server.blpop("logging")
        logging.info(s[1].decode("UTF-8"))

def CheckinAffairsThreadWorker(server):
    """
        解决checkin的重复扣费问题,
        成功的话必须走checkinresult通道！
        Checkin Result Bundle
        {
            user:123,
            id:123,#这里的id指的是选座的id，防止重复扣费用.
            username:xxx,
            school:xxx
        }
    """
    logging.info("已加载CheckinAffairs Thread Worker"+threading.current_thread().getName())
    initdb = sqlite3.connect("data/db/sqlite.db")
    initdb.row_factory = sqlite3.Row
    while True:
        try:
            cursor = initdb.cursor()
            info = pickle.loads(server.blpop("checkin_result")[1])
            logging.info(str(info))
            result_have_checkin = server.get(str(info['id'])) 
            result_settings = cursor.execute("select * from settings where user = ? ",(info['user'],)).fetchone()
            if result_have_checkin == None:
                logging.info("user"+str(info['user'])+"进行扣款操作")
                #进行扣款操作
                lastAmount = result_settings['checkin']
                if lastAmount == -1:#无限玩家
                    pass
                else:
                    lastAmount = 0 if lastAmount - PREMIUM_CHECKIN_AUTO < 0 else lastAmount - PREMIUM_CHECKIN_AUTO
                #写入扣款
                cursor.execute("update settings set checkin = ? where user = ?",(lastAmount,info['user'],))
                #写入显示log
                cursor.execute("insert into log (user,jigann,content,type) values(?,?,?,?)",(info['user'],datetime.today().__str__(),"[{0},{1}]签到成功".format(info['username'],info['school']),10,))
                #写入redis
                server.set(str(info['id']),"1",ex=7200)
            else:
                #写入显示log
                cursor.execute("insert into log (user,jigann,content,type) values(?,?,?,?)",(info['user'],datetime.today().__str__(),"[{0},{1}]重新签到成功，不扣除点数".format(info['username'],info['school']),10,))
            logging.debug(info)
        except redis.exceptions.ConnectionError as e:
            logging.critical(e)
            time.sleep(5)
        except Exception as e:
            logging.error(e)
        finally:
            logging.info("SQL THREAD WORK 已经执行一次提交"+threading.current_thread().getName())
            initdb.commit()
            cursor.close()
    initdb.close()

def sqlThreadWorker(server):
    """
        Automatic sql executor using a Thread Queue.
    """
    logging.info("已加载SQL THREAD WORKER"+threading.current_thread().getName())
    initdb = sqlite3.connect("data/db/sqlite.db")
    initdb.row_factory = sqlite3.Row
    while True:
        try:
            cursor = initdb.cursor()
            info = pickle.loads(server.blpop("sql")[1])
            cursor.execute(info['sql'],info['args'])
            logging.debug(info)
        except redis.exceptions.ConnectionError as e:
            logging.critical(e)
            time.sleep(5)
        except Exception as e:
            logging.error(e)
        finally:
            logging.info("SQL THREAD WORK 已经执行一次提交"+threading.current_thread().getName())
            initdb.commit()
            cursor.close()
    initdb.close()


###########################################################################################
# Main Deploy.
def deploy(duration=15,processNumber=None,standalone=False,redis_addr='127.0.0.1'):
    #REDIS
    try:
        server = redis.Redis(host=redis_addr)
        logging.debug(server.info())
        logging.info("redis server "+redis_addr+"connected.")
    except Exception as e:
        logging.critical(e)
        logging.critical("服务系统强制退出")
        exit(2)
    #deploy the thread workers
    sqlthread = Thread(target=sqlThreadWorker,name="sql Thread worker",args=(server,))
    sqlthread.daemon = True
    sqlthread.start()

    # depoly checkin user fetch worker. #队列线程
    userthread = Thread(target=getAllCheckinUserWorker,args=(server,duration,))
    userthread.daemon = True
    userthread.start()

    #deploy auto reservation fetch worker; #队列线程
    userthread_reserve = Thread(target=getAllAutoReservationUserWorker,args=(server,))
    userthread_reserve.daemon = True
    userthread_reserve.start()

    #deploy logging thread

    loggingthread = Thread(target=loggingThreadWorker,args=(server,))
    loggingthread.daemon = True
    loggingthread.start()

    #deploy checkinaffairs thread
    checkinthread = Thread(target=CheckinAffairsThreadWorker,args=(server,))
    checkinthread.daemon = True
    checkinthread.start()

    if standalone:
        spawnProcess(processNumber,redis_addr)
    else:
        logging.info("***非独立模式***,只开启服务响应以及服务派发器")    

    logging.info("***分布式协作接口开启***")
    logging.info("***Distributed Cooperating Interface is Deployed.*** ")
    import gc  
    # import objgraph  
    # ### 强制进行垃圾回收  
    # gc.collect()  
    # ### 打印出对象数目最多的 50 个类型信息  
    # objgraph.show_most_common_types(limit=50)  
    sqlthread.join()

def spawnProcess(processNumber,redis_addr="127.0.0.1"):
    """
       for multiprocess
    """
    if processNumber == None:
        processNumber = os.cpu_count()
        if processNumber == None:
            processNumber = 1
    _fin_n = 2 if processNumber <= 2 else processNumber
    logging.info("use {0} processes".format(processNumber))
    _pool = Pool(processes = _fin_n) #进程池
    for _ in range(_fin_n):
        _pool.apply_async(doAutoCheckinWork,(redis_addr,))
        _pool.apply_async(doAutoReserveWork,(redis_addr,))
    logging.info("进程部署完毕")
    return _pool
    

def clientDeploy(address=None,processNumber = None):
    """
        A method like deploy. But it runs in client role.
        just spawns processes and runs local proxy for remote execution
        do not run client and server role at the same time!
    """
    """
       for multiprocess
    """
    return spawnProcess(processNumber,address)

def doAutoCheckinWork(serverAddr):
    try:
        time.sleep(1)
        logging.info("正在连接***"+serverAddr)
        server = redis.Redis(host=serverAddr)
        server.rpush("logging","*** 有外部Work接入啦！")
        logging.info("SUCCESS***"+serverAddr)
        obj = None
        while True:
            info = pickle.loads(server.blpop("checkin")[1])
            server.rpush("logging",str(dict(info))+ "=========" + str(os.getpid()))
            try:
                if CAMPUS_CHECKIN_ENABLED(CAMPUS(info['school'],info['auto_checkin'])):
                    obj,result = SeatClient.quickCheckin(info['school'],info['auto_checkin'],info['username'],info['password'],info['id'],info['token'],None) #严禁重用对象！
                    if result:
                        server.rpush("checkin_result",pickle.dumps({'id':result['id'],'user':info['id'],'username':info['username'],'school':info['school']}))
                        # localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到成功".format(info['username'],info['school']),10,))
                        # localExecuteProxy(server,"update settings set checkin = ? where user = ?",(targetAmount,info['id']))
                    time.sleep(3)
            except SeatReservationException as e:
                #failed
                if e == SeatReservationException.NO_AVAILABLE_RESERVATIONS or e == SeatReservationException.RESERVE_HAVE_CHECKEDIN:
                    pass
                else:
                    localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到失败，{2}".format(info['username'],info['school'],e.message),LOG_STATUS_CHECKIN))
               
            except Exception as e:
                localExecuteProxy(server,"insert into log (user,jigann,content,type) values(?,?,?,?)",(info['id'],datetime.today().__str__(),"[{0},{1}]签到错误，{2}".format(info['username'],info['school'],e),LOG_ERR_CHECKIN))
                server.rpush("logging",str(e))
    except Exception as e:
        print(e)
    finally:
        pass

def doAutoReserveWork(serverAddr):
    """
        执行占座任务 4点55登录，4.56开始预约
    """
    ##使用协程gevent 库 废弃，对这个不友好！
    # import gevent
    # from gevent import monkey
    # # monkey.patch_socket()
    # monkey.patch_builtins()
    # monkey.patch_time()
    logging.info("自动约座进程{0}已开启..".format(str(os.getpid())))
    logging.info("正在连接***"+serverAddr)
    time.sleep(1)#wait for server.
    retry_threshold = 500 #最大错误阈值
    try:
        #连接分布式服务器。
        server = redis.Redis(host=serverAddr)
        logging.info("SUCCESS***"+serverAddr)
        server.rpush("logging","***已加载一个分布式自动约座组件进程***"+str(os.getpid()))
    except Exception as e:
        print(e)
    def doFinished(server,user,seat,person):
        logToRemote(server,user,"已成功预约,{0}".format(seat['name']),LOG_OK_RESERVATION)
        #扣款
        targetAmount = user['reserve']
        if user['reserve'] == -1: #无限玩家
            pass
        elif user['reserve'] > 0:
            targetAmount = 0 if user['reserve'] - PREMIUM_RESERVE_AUTO <= 0 else user['reserve'] - PREMIUM_RESERVE_AUTO  
        localExecuteProxy(server,"update settings set reserve = ? where user = ? ",(targetAmount,user['id'],))
        
    def process(userBody):
        #每人一个小线程，时间耗在IO。
        #肯定len >= 1否则数据库查不出来
        user = userBody['user'] # 用户信息
        seats = userBody['seats'] # 用户位置
        retry = 0
        person = None
        statusOk = False
        #开始第一阶段
        ######
        # 时间控制
        # BUG 修复： 每次创建线程要先做好刷新stage
        #####
        stage_1_time = datetime.today().replace(hour=4,minute=55,second=0) #登录时间
        stage_2_time = datetime.today().replace(hour=4,minute=59,second=57) #抢座时间
        logging.info("***{0} process 开始第一阶段！***".format(user['username']))
        # time.sleep(1000)
        delta = parseDateWithTz(stage_1_time) - getServerTimePRC(SCHOOL(user['school'])['BASE']) #第一阶段时间减去服务器时间。
        logging.info("正在等待至第一阶段进行登录,"+str(delta.days * 86400 + delta.seconds)+"秒...")
        time.sleep(delta.days * 86400 + delta.seconds if delta.days * 86400 + delta.seconds > 0 else 0)
        loginCount = 0
        while True:
            try:
                person = SeatClient.NewClient(user['username'],user['password'],campus=CAMPUS(user['school']),school=user['school'])
                break
            except UserCredentialError as e:
                if loginCount > 10:
                    #登录之类的事情都在这里
                    logToRemote(server,user,"自动预约失败,登陆异常({0})".format(e),LOG_ERR_RESERVATION)
                    return
                else:
                    loginCount += 1
                    time.sleep(5)
                    continue
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
        logging.info("正在等待至第二阶段进行登录,"+str(delta.days * 86400 + delta.seconds)+"秒...")
        time.sleep(delta.days * 86400 + delta.seconds if delta.days * 86400 + delta.seconds > 0 else 0)
        # person.login() #强制重新登录
        loginCount = 0
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
                            doFinished(server,user,seat,person)
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
                        except UserCredentialError as err:
                                if loginCount > 5:
                                    #登录之类的事情都在这里
                                    logging.warning("ERROR"+str(err))
                                    logToRemote(server,user,"自动预约失败,登陆异常({0})".format(err.type),LOG_ERR_RESERVATION)
                                    return
                                else:
                                    loginCount += 1
                                    time.sleep(0.5)
                                    continue
                        except Exception as err:
                            #可能是网络等问题
                            if "参数错误" in str(err):
                                 logToRemote(server,user,"自动预约失败,{0}".format(str(err)),LOG_DEBUG_RESERVATION)
                                 print("退出")
                                 return
                            logToRemote(server,user,"自动预约失败,{0}".format(str(err)),LOG_DEBUG_RESERVATION)
                            if timelimit > 1:
                                time.sleep(0.9)
                            else:
                                time.sleep(timelimit)
                                timelimit += 0.1
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
    _t_poll = TPool(processes=200) #注意，以后要扩增多台
    try:
        while True:
            body = pickle.loads(server.blpop("reserve")[1])
            _t_poll.apply_async(process,(body,))
            time.sleep(0.5)
    except Exception as e:
        print(e)
       

            
    

def getAllCheckinUserWorker(server,duration = 30,):
    """
        获取所有学生的信息，注入queue
    """
    logging.info("已加载获取自动签到子进程 GET ALL USER CHECKIN WORKER"+threading.current_thread().getName())
    time.sleep(10) # 等10秒
    initdb = sqlite3.connect("data/db/sqlite.db") 
    initdb.row_factory = sqlite3.Row
    while True:
        if datetime.today().hour > 22 or datetime.today() < datetime.today().replace(hour=6,minute=45):
            time.sleep(60)
            continue
        logging.info(threading.current_thread().getName()+"执行一次用户抓取用于签到")
        try:
            cursor = initdb.cursor()
            for i in cursor.execute(SQL_ALL_AUTOCHECKIN_PERSON):
                server.rpush("checkin",pickle.dumps(dict(i)))
                time.sleep(1)
            time.sleep(duration*60)
        except Exception as err:
            logging.error(err)
        finally:
            cursor.close()
            time.sleep(10)
    initdb.close()

def getAllAutoReservationUserWorker(server):
    """
      获取所有 占座用户 在4点半开始执行。
      向队列释放用户

      BUG 在一个游标里面进行execute会爆炸
    """
    logging.info("已加载自动约座。GET ALL USER RESERVATION WORKER"+threading.current_thread().getName())
    logging.info("正在等待数据投放时间（4.30）"+threading.current_thread().getName())
    while True: # 每天一个循环。
        try:
            if datetime.today().hour == 4 and datetime.today().minute == 30:
                logging.info("启动一次用户约座部署器。GET ALL USER RESERVATION WORKER"+threading.current_thread().getName())
            else:
                time.sleep(30)
                continue
            initdb = sqlite3.connect("data/db/sqlite.db") #开启数据库
            initdb.row_factory = sqlite3.Row
            userList = []
            cursor = initdb.cursor()
            #获取开通自动占座的用户，
            for i in cursor.execute(SQL_ALL_RESERVATION_PERSON):
                logging.info("预约座位用户注入："+str(i['user']))
                userList.append(i)
            #获取占座用户的seat
            for i in userList:
                _resultBundle = [dict(x) for x in cursor.execute(SQL_ALL_RESERVATION_SEATS,(i['user'],)) ] 
                logging.info("用户ID{0}获取了{1}个预选座位".format(i['user'],len(_resultBundle))+threading.current_thread().getName())
                #如果预选座位为空，就跳过
                if len(_resultBundle) == 0:
                    continue
                server.rpush("reserve",pickle.dumps({'seats':_resultBundle,'user':dict(i)}))
                logging.info("约座部署器部署完毕。GET ALL USER RESERVATION WORKER"+threading.current_thread().getName())
            cursor.close()
            initdb.close()
            time.sleep(3600) #防止重复部署
        except Exception as err:
            logging.error(err)
            
   



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
    payload = {
        "sql":sqlstr,
        "args":args
    }
    server.rpush("sql",pickle.dumps(payload))
    # server.blpop()

