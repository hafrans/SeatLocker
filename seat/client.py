
"""
    Future Features of Seat Client

"""


import urllib
import urllib.parse
import urllib.request
import re
import json
import logging
from datetime import datetime, timedelta, time
from .exception import *
from .request import *
from .constant import *

__all__ = ['SeatClient']



"""
    constants
"""

AUTH                = "AUTH"
RESERVATIONS        = "RESV"
FREE_FILTER         = "FFTR"
ROOM_STAT           = "RMST"
ROOM_LAYOUT_BY_DATE = "LOBD"
START_TIME_FOR_SEAT = "STFS"
END_TIME_FOR_SEAT   = "ETFS"
FREE_BOOK           = "BOOK"
CHECK_IN            = "CKIN"
STOP                = "STOP"
HISTORY             = "HSTY"
CANCEL              = "CACE"


class SeatClient(object):
    """
        SeatClient
        seat client is a virual client api for seat reservation system of ujn.
        It provides lots of methods can book seat and check in
    """

    @staticmethod
    def NewClient(username, password,campus = CAMPUS(UNIVERSITY_OF_JINAN),school=UNIVERSITY_OF_JINAN):
        return SeatClient({'username': username, 'password': password},campus=campus,school=school)
    
    @classmethod
    def deserialize(SeatClient,sourceObj):
        """
            deserialize SeatClient instance from json.
            :param sourceObj: json which described details of Seatclient.
            :return SeatClient instance
        """
        _meta = json.loads(sourceObj)
        clazz = SeatClient(profile=_meta['profile'],campus=_meta['campus'],school=_meta['school'],autoLogin=False)
        clazz.opener.token = _meta['token']
        clazz.__SeatClient__isLogin = _meta['isLogin']
        clazz.id = _meta["id"]

        return clazz

    def serialize(self):
        """
            Serialize the instance to a json string.
            :return a descriptor of this instance using json. 
        """
        payload = {
            "profile":self.profile,
            "token":self.opener.token,
            'campus':self.opener.region,
            "school":self.school,
            "isLogin":self.__isLogin,
            "id": self.__id
        }
        return json.dumps(payload)
    
    @staticmethod
    def NewClientFromSession(session):
        """
            helper of initializing instance
            :param session: session of flask.
            :return a instance of SeatClient
        """
        if session.get('entity',None) == None:
            raise Exception("Session Entity:None")
        return SeatClient.deserialize(session.get('entity'))

    @staticmethod
    def quickCheckin(schoolName,campusId,username,password,id,sourceObj = None):
        """
            Helper of autochecking in. this method could reuse instance of object if it could.
            :param schoolName: school name 
            :param campusId: It represented an id of a campus of college of univerisity.
        """
        if sourceObj == None:
            sourceObj = SeatClient.NewClient(username=username,password=password,campus=CAMPUS(schoolName,campusId),school=schoolName)
        else:
            if id != sourceObj.id:
                sourceObj.profile = {'username':username,'password':password}
                sourceObj.campus = CAMPUS(schoolName,campusId)
                sourceObj.id = id
                sourceObj.school = schoolName
            sourceObj.login()
        result = sourceObj.checkIn()
        return sourceObj,result
        

    def __init__(self, profile, campus = CAMPUS(UNIVERSITY_OF_JINAN),school = UNIVERSITY_OF_JINAN, autoLogin=True):
        """
            initialize instance of SeatClient.
            :param profile user's profile {'username'：xxx, 'password':xxx}
            :param campus the user's region of campus 
            :param autoLogin bool auto login when initializing
        """
        self.__id = 0
        self.opener = WrappedRequest(campus,school)
        self.profile = profile
        self.school = school
        self.__isLogin = False
        self.__last_error_message = ""

        logging.info("%s 使用了 %s %s 登录。",profile['username'],SCHOOL(school)['NAME'],campus['name'])

        if autoLogin:
            logging.info("开启了默认登录 %s", profile['username'])
            self.login()

    def getLastError(self):
        return self.__last_error_message

    def checkStatus(self, result):
        self.__last_error_message = result['message']

        if result['status'] == 'success' and result['code'] == '0':
            return True
        elif result['status'] == 'fail' and result['message'] == 'System Maintenance':
            logging.critical("目标系统正在维护 [%s] %s",
                             self.profile['username'], result)
            self.__last_error_message = result['message']
            raise SystemMaintenanceError("目标系统正在维护 "+result['message'])

        elif result['code'] == '13':
            logging.warning("登录失败 [%s] %s", self.profile['username'], result)
            self.__last_error_message = result['message']
            self.__isLogin = False
            raise UserCredentialError(result['message'])
        
        elif result['code'] == '12':
            logging.warning("登录失败 -- TOKEN 失效 [%s] %s", self.profile['username'], result)
            self.__last_error_message = result['message']
            self.__isLogin = False
            raise UserCredentialError(result['message'],UserCredentialError.TOKEN_EXPIRED)

        elif result['code'] == '1':  # 错误有很多种类

            if result['message'] == "预约失败，请尽快选择其他时段或座位":
                logging.warning(
                    "预约失败 [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.FAILED_RESERVED)

            elif result['message'] == "已有1个有效预约，请在使用结束后再次进行选择":
                logging.warning(
                    "预约失败 [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.HAVE_RESERVED)

            elif result['message'] == "当前没有可用预约":
                logging.warning(
                    "checkin失败！ [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.NO_AVAILABLE_RESERVATIONS)

            elif result['message'] == "请连接此场馆无线网或在触屏机上操作":
                logging.warning(
                    "checkin失败！ [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.IP_NOT_ALLOWED)
            
            elif result['message'] == "预约已经取消，请勿重复操作":
                logging.warning(
                    " [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.RESERVE_HAVE_CANCELED)
            
            elif result['message'] == "无效预约":
                logging.warning(
                    " [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.RESERVE_CANCEL_INVALIDED)
            elif "系统可预约时间为" in result['message']:
                logging.warning(
                    " [%s] %s", self.profile['username'], result)
                raise SeatReservationException(result['message'],SeatReservationException.NOT_IN_RESERVE_TIME)
            elif result['message'] == "许可证已过期":
                logging.critical(
                    " [%s] %s", self.profile['username'], result)
                raise SeatReservationException("图书馆座位系统"+result['message'],SeatReservationException.LICENSE_EXPIRED)

            else:
                logging.warning(
                    "参数错误 [%s] %s", self.profile['username'], result)
                raise Exception("{0}".format(result['message']))
            
        else:
            logging.critical(
                "无法预料的错误 [%s] %s", self.profile['username'], result['message'])
            raise Exception("Unknown Error! {0}".format(result['message']))
    
    def getSeatRoomBundle(self,roomId,seatId,campus=None):
        """
            using room id and seat id fetch all information about this seat
            :param roomId: roomid
            :param seatid: seatid 
        """
        if campus == None:
            campus = self.campus
        targetString = campus['name']
        roomList = self.getRoomStatus(campus)
        for i in roomList:
            if i['roomId'] == roomId:
                targetString += str(i['floor'])+"层"
                targetString += i['room']
                break
        else:
            logging.warning("没找到相关房间 %d",roomId)
            # return None
            raise RoomNotFoundException()
        seatList = self.getSeatsInRoomWithRoomId(roomId)
        for i in seatList['layout'].values():
            if i['type'] == 'seat' and i['id'] == seatId :
                targetString += "第"+i['name']+"号位"
                break           
        else:
            logging.warning("没找到相关座位 %d",seatId)
            # return None
            raise SeatNotFoundException()
        return targetString

    @property
    def campus(self):
        return self.opener.region

    @campus.setter
    def campus(self, val):
        self.opener.region = val

    @property
    def token(self):
        return self.opener.token

    @token.setter
    def token(self, val):
        self.opener.token = val

    @property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self,val):
        self.__id = val

    def login(self):
        """
            User Login 

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

        """
        result = None
        try:
            result = self.opener.request(
                AUTH, payload=self.profile, append_mode=True)
            logging.info(result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        if self.checkStatus(result):
            # 登录成功
            logging.info(
                "登录成功 [%s] %s", self.profile['username'], result['data']['token'])
            # 保存用户token
            self.token = result['data']['token']
            self.__isLogin = True
            return True
        else:
            return False

    def getReservations(self):
        """
            Get a List of Your Reservations.

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            Returns: 
                [{'id': 596777, 'receipt': '42as-6', 'onDate': '2019-03-23', 'seatId': 8035, 'status': 'RESERVE', 'location': '西校区7层703室区第六阅览室北区，座位号122', 'begin': '09:00', 'end': '22:00', 'actualBegin': None, 'awayBegin': None, 'awayEnd': None, 'userEnded': False, 'message': '请在 03
月23日08点15分 至 09点15分 之间前往场馆签到'}]

        """
        result = None
        try:
            result = self.opener.request(RESERVATIONS)
            logging.info("get reservations %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        if self.checkStatus(result):
            if result['data'] == None:
                logging.debug("获取了0条已预约的座位数据  [%s] ", self.profile['username'])
                return []
            else:
                logging.info(result['data'])
                str = """   
                            卡号： %s
                            使用中的位置：{0}
                            状态：{1}，日期：{2}，
                            开始：{3}，结束：{4}，
                            提示：{5}
                    """
                logging.info(str.format(result['data'][0]['location'], result['status'], result['data'][0]['onDate'],
                                        result['data'][0]['begin'], result['data'][0]['end'], result['data'][0]['message']), self.profile['username'])
                return result['data']

    def getReservationAvailableDates(self):
        """
           get reservation available dates

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            Param campus choose west or east campus using defined constant.

            Returns:
              list of dates like ['2019-03-23', '2019-03-24']

        """
        result = None
        try:
            result = self.opener.request(FREE_FILTER)
            logging.info("get dates %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        if self.checkStatus(result):
            logging.debug("可预约时间 %s", result['data']['dates'])
            return result['data']['dates']

    def getRoomStatus(self, campus=None):
        """
           get all rooms status

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            Param campus choose west or east campus using defined constant.

            Returns:
              list of room with infos. look at debug info
              {'roomId': 25, 'room': '第六阅览室南区', 'floor': 7, 'maxHour': 15, 'reserved': 0, 'inUse': 100, 'away': 0, 'totalSeats': 108, 'free': 8}

        """

        result = None
        payload = {
            "campus": self.campus['id'] if campus == None else campus['id']
        }
        try:
            result = self.opener.request(ROOM_STAT, payload=payload)
            logging.debug("get free rooms %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)

        # # print all list
        # for i in result['data']:
        #     logging.debug(i)
        if result['data'] == None:
            result['data'] = []
        return result['data']

    def getSeatsInRoomWithRoomId(self, roomId, layoutDate=None):
        """
           get all seats status with roomid 

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            Param roomId required. the id of room which you want to get seats' status.
            :param layoutDate: 要预定的日期字符串，格式为 yyyy-mm-dd
            Returns:
              list of seats with infos. look at debug info


        """
        if layoutDate == None:
            layoutDate = str((datetime.today() + timedelta(days=0)).date())

        result = None
        payload = {
            "roomId": roomId,
            "date": layoutDate
        }
        try:
            result = self.opener.request(ROOM_LAYOUT_BY_DATE, payload=payload)
            logging.debug("get seats  %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)

        # print all list
        for k, v in result['data'].items():
            logging.debug("%s : %s", k, v)

        """
            id , name , cols , row12 ,layout{key:{type = 'seat' name='001' status='FREE|IN_USE?',}}
        """

        return result['data']

    def getSeatStartTimeWithSeatId(self, seatId, layoutDate=None):
        """
           get Seat Start Times with seat Id

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            :param seatId: required. the id of room which you want to get seats' status.
            :param layoutDate: 要预定的日期字符串，格式为 yyyy-mm-dd 默认是明天
            Returns:
            时间序列[{'id': '420', 'value': '07:00'}]等，如果为空，则当天无法预定

        """
        if layoutDate == None:
            layoutDate = str((datetime.today() + timedelta(days=1)).date())
        result = None
        payload = {
            "seatId": seatId,
            "date": layoutDate
        }
        try:
            result = self.opener.request(START_TIME_FOR_SEAT, payload=payload)
            logging.debug("get %s  %s", self.getSeatStartTimeWithSeatId, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("getstart %s %s %s", self.getSeatStartTimeWithSeatId,
                      layoutDate, result['data']['startTimes'])
        return result['data']['startTimes']

    def getSeatEndTimeWithSeatId(self, seatId, startTime, layoutDate=None):
        """
           get Seat End Times with seat Id

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            :param seatId: required. the id of room which you want to get seats' status.
            :param layoutDate: 要预定的日期字符串，格式为 yyyy-mm-dd 默认是明天
            :param startTime: required start time of seat.
            Returns:
            时间序列 [{'id': '420', 'value': '07:00'}]等，如果为空，则当天无法预定

        """
        if layoutDate == None:
            layoutDate = str((datetime.today() + timedelta(days=1)).date())
        result = None
        payload = {
            "seatId": seatId,
            "date": layoutDate,
            "startTime": startTime
        }
        try:
            result = self.opener.request(END_TIME_FOR_SEAT, payload=payload)
            logging.info("get %s  %s", self.getSeatEndTimeWithSeatId, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.getSeatEndTimeWithSeatId,
                      result['data']['endTimes'])
        return result['data']['endTimes']

    def reserveSeat(self, seatId, startTime=480, endTime=1320, layoutDate=None, tuesdayType=False):
        """
           get Seat End Times with seat Id

            Errors:
              Exception Unknown Exception Raised By Urilib
              NetWorkException 其他状态导致的网络有问题，比如刷的太快
              UserCredientialError 用户登录失败或状态失败
              SystemMaintenanceError 系统维护导致失败

            :param seatId: required. the id of room which you want to get seats' status.
            :param layoutDate: 要预定的日期字符串，格式为 yyyy-mm-dd 默认是明天
            :param startTime: required start time of seat.
            :param endTime: required end time of seat
            :param tuesdayType: 周二策略，如果为True，则周二会约 12 点之前的时间段，False为约16点之后的时间段

            Returns:
            时间序列 [{'id': '420', 'value': '07:00'}]等，如果为空，则当天无法预定

        """
        if layoutDate == None:
            layoutDate = str((datetime.today() + timedelta(days=1)).date())

        # 判断用户预输入的时间的正确或错误
        if startTime >= endTime:  # 判断初始时间是否合法
            logging.error("初始结束时间不合法！%s [%s] ([%s] %s %s)", self.reserveSeat,
                          self.profile['username'], layoutDate, startTime, endTime)
            raise SeatReservationException("初始结束时间不合法！",SeatReservationException.TIME_SPAN_ERROR)
        # 判断周二策略
        if datetime(*[int(x) for x in layoutDate.split('-')]).weekday() == 1:
            logging.info("现在是周二")
            if startTime >= 720 and endTime <= 960:
                logging.error("周二无法在您规定时间段内预约座位 %s [%s] ([%s] %s %s)", self.reserveSeat,
                              self.profile['username'], layoutDate, startTime, endTime)
                raise SeatReservationException("周二无法在您规定时间段内预约座位！",SeatReservationException.TIME_SPAN_ERROR)
            if tuesdayType == True:  # 执行上午策略
                logging.info("执行上午策略")
                if startTime < 720 and endTime >= 720:
                    endTime = 720
            else:  # 下午策略
                logging.info("执行下午策略")
                if startTime < 960 and endTime >= 960:
                    startTime = 960
            # 最终处理
            if endTime > 720 and endTime < 960:
                endTime = 720
            if startTime > 720 and startTime < 960:
                startTime = 960

        if startTime >= endTime:  # 判断处理后的时间是否合法
            logging.error("处理后初始结束时间不合法（2）！%s [%s] ([%s] %s %s)", self.reserveSeat,
                          self.profile['username'], layoutDate, startTime, endTime)
            raise SeatReservationException("初始结束时间不合法！",SeatReservationException.TIME_SPAN_ERROR)
        logging.debug("最终时间 %s [%s] ([%s] %s %s)", self.reserveSeat,
                      self.profile['username'], layoutDate, startTime, endTime)
        postForm = {
            'startTime': startTime,
            'endTime': endTime,
            'seat': seatId,
            'date': layoutDate
        }
        result = None
        try:
            result = self.opener.request(FREE_BOOK, post=postForm)
            logging.info("get %s  %s", self.reserveSeat, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.reserveSeat, result['data'])
        return result['data']
    
    def checkIn(self):
        """
           开始预约
           注意：某些账户，进入图书馆不需要手动签到就可以自动签
           要先通过getreservations获得status 是不是 RESERVE,或者CHECK_IN
        """

        """
        两次获取，看看会不会自动签到
        """
        _tmp_result = self.getReservations()
        if  len(_tmp_result) > 0 and  _tmp_result[0]['status'] == "CHECK_IN":
            logging.info("已经实现自动签到 %s", self.checkIn)
            raise SeatReservationException("已经签到成功，无需再次签到",SeatReservationException.RESERVE_HAVE_CHECKEDIN)

        result = None
        try:
            result = self.opener.request(CHECK_IN,forwardIP=True)
            logging.info("get %s  %s", self.checkIn, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.checkIn, result['data'])
        return result['data']
    
    def stop(self):
        """
            结束使用座位
        """
        result = None
        try:
            result = self.opener.request(STOP)
            logging.info("get %s  %s", self.stop, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.stop, result['data'])
        return True
    
    def getHistory(self):
        """
         获取日志记录
        """
        result = None
        try:
            result = self.opener.request(HISTORY)
            logging.info("get %s  %s", self.getHistory, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.getHistory, result['data']['reservations'])
        return result['data']['reservations']
    
    def cancel(self,id):
        """
            取消预约
        """
        result = None
        payload = {
            'id':id
        }
        try:
            result = self.opener.request(CANCEL,payload=payload)
            logging.info("get %s  %s", self.cancel, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s", self.cancel, result['data'])
        return True
