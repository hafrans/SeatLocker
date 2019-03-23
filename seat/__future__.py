#!/usr/bin/python3
# -*- coding:utf8 -*-

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


logging.basicConfig(level=logging.DEBUG,
                    format="[%(levelname)s] %(asctime)s - %(message)s")


__all__ = ['SeatClient']

EAST_CAMPUS = "10.167.149.241"  # WHO CAN PROVIDE ME A IP OF EC?
WEST_CAMPUS = "10.167.149.242"


"""
    constants
"""

AUTH = "AUTH"
RESERVATIONS = "RESV"
FREE_FILTER = "FFTR"
ROOM_STAT = "RMST"
ROOM_LAYOUT_BY_DATE = "LOBD"
START_TIME_FOR_SEAT = "STFS"
END_TIME_FOR_SEAT = "ETFS"


class NetWorkException(Exception):
    pass


class SystemMaintenanceError(Exception):
    pass


class UserCredentialError(Exception):
    pass

class SeatReservationException(Exception):
    pass


class WrappedRequest(object):
    """
        WrappedRequest Class
        This class provides a delegation for urllib.
    """

    BASE_URL = "http://seat.ujn.edu.cn"

    ROUTER = {
        "AUTH": "/rest/auth",
        "RESV": "/rest/v2/user/reservations",
        "FFTR": "/rest/v2/free/filters",
        "RMST": "/rest/v2/room/stats2/{campus}",
        "LOBD": "/rest/v2/room/layoutByDate/{roomId}/{date}",
        "STFS": "/rest/v2/startTimesForSeat/{seatId}/{date}",
        "ETFS": "/rest/v2/endTimesForSeat/{seatId}/{date}/{startTime}",
        "BOOK": "/rest/v2/freeBook"
    }

    __default_headers_template = {
        "Host": urllib.parse.urlparse(BASE_URL).netloc,
        "Connection": "Keep-Alive",
        "User-Agent": "",
        "X-Forwarded-For": "",  # add this
        "token": ""
    }

    def __init__(self, campus=WEST_CAMPUS):
        """
        initialize instance with correct headers
        """
        self.headers = WrappedRequest.__default_headers_template
        self.opener = urllib.request.urlopen
        pass

    @staticmethod
    def makeQuickCheckIn(token):
        pass

    @property
    def region(self):
        """
          get the region of campus west or east or other
        """
        if self.headers['X-Forwarded-For'] == WEST_CAMPUS:
            return "WEST_CAMPUS"
        elif self.headers['X-Forwarded-For'] == EAST_CAMPUS:
            return "EAST_CAMPUS"
        else:
            return self.headers['X-Forwarded-For']

    @region.setter
    def region(self, campus=WEST_CAMPUS):
        """
          set the region of campus west or east or other
        """
        if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", campus):
            self.headers['X-Forwarded-For'] = campus
        else:
            logging.warning("set region failed %s", str(campus))

    @property
    def token(self):
        """
          get token which could identify one's status
        """
        return self.headers['token']

    @token.setter
    def token(self, token):
        """
        set token
        :param token the token you will set.
        """
        if len(token) < 5:
            return False
        else:
            self.headers['token'] = token
            return True

    def urlencode(self, payload={}, charset="UTF-8"):
        return urllib.parse.urlencode(payload, encoding=charset)

    def request(self, route=None, url=None, payload=None, post=None, append_mode=False):
        """
            Send Request To Server.
        """
        url_route_flag = False
        _url = ""
        _data = ""
        _post = None
        request = None

        if route == None and url == None:
            raise AttributeError("either route or url is not specified")
        if route != None:
            _url = WrappedRequest.ROUTER.get(route, None)
            if _url == None:
                raise AttributeError("Route name Not Found!")
            _url = WrappedRequest.BASE_URL + _url
        elif url != None:
            _url = url
            url_route_flag = True

        if payload != None:
            _data = self.urlencode(payload)

        if post != None:
            _post = str.encode(self.urlencode(post), encoding='UTF-8')

        if url_route_flag or append_mode:  # use url
            request = urllib.request.Request(
                _url + "?" + _data, data=_post, headers=self.headers)
            logging.debug("send request to %s", _url)
        elif payload != None:
            request = urllib.request.Request(_url.format(
                **payload), data=_post, headers=self.headers)
            logging.debug("send request to %s", _url.format(**payload))
        else:
            request = urllib.request.Request(
                _url, data=_post, headers=self.headers)
            logging.debug("send request to %s with %s", _url, post)

        resp = self.opener(request)

        if resp.status == 200 and resp.getheader("Content-Length") != "0":
            return json.load(resp)
        else:
            raise NetWorkException("Network Error ({0},{1},{2})".format(
                resp.status, resp.getheader("Content-Length"), resp.read()))


class SeatClient(object):

    @staticmethod
    def NewClient(username, password):
        return SeatClient({'username': username, 'password': password})

    def __init__(self, profile={'username', 'password'}, campus=WEST_CAMPUS, autoLogin=True):
        """
            initialize instance of SeatClient.
            :param profile user's profile
            :param campus the user's region of campus 
            :param autoLogin bool auto login when initializing
        """

        if campus == WEST_CAMPUS:
            logging.info("使用的是西校的配置进行登录 %s", profile['username'])
        elif campus == EAST_CAMPUS:
            logging.info("使用的是东校的配置进行登录 %s", profile['username'])
        else:
            logging.info("使用的是其他的配置进行登录 %s (%s)", profile['username'], campus)

        self.opener = WrappedRequest()
        self.opener.region = campus
        self.profile = profile
        self.__isLogin = False
        self.__last_error_message = ""

        if autoLogin:
            logging.info("开启了默认登录 %s", profile['username'])
            self.login()

    def getLastError(self):
        return self.__last_error_message

    def checkStatus(self, result):
        if result['status'] == 'success' and result['code'] == '0':
            return True
        elif result['status'] == 'failed' and result['message'] == 'System Maintenance':
            logging.critical("目标系统正在维护 [%s] %s",
                             self.profile['username'], result)
            self.__last_error_message = result['message']
            raise SystemMaintenanceError(result['message'])
        elif result['code'] == '13':
            logging.warning("登录失败 [%s] %s", self.profile['username'], result)
            self.__last_error_message = result['message']
            raise UserCredentialError(result['message'])
        else:
            logging.critical(
                "无法预料的错误 [%s] %s", self.profile['username'], result['message'])
            raise Exception("Unknown Error! {0}".format(result['message']))

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

        def checkCampus(campus):
            if campus == None:
                return checkCampus(self.campus)
            if campus == "WEST_CAMPUS" or campus == WEST_CAMPUS:
                return 2
            elif campus == EAST_CAMPUS or campus == "EAST_CAMPUS":
                return 1
            else:
                logging.warning("未知的校区错误 [%s] %s",
                                self.profile['username'], str(campus))
                return 1

        result = None
        payload = {
            "campus": checkCampus(campus)
        }
        try:
            result = self.opener.request(ROOM_STAT, payload=payload)
            logging.info("get free rooms %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)

        # print all list
        for i in result['data']:
            logging.info(i)

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
            logging.info("get seats  %s", result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)

        # print all list
        for k, v in result['data'].items():
            logging.info("%s : %s", k, v)

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
            logging.info("get %s  %s",self.getSeatStartTimeWithSeatId, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s",self.getSeatStartTimeWithSeatId, result['data']['startTimes'])
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
            logging.info("get %s  %s",self.getSeatEndTimeWithSeatId, result)
        except NetWorkException as e:
            logging.warning("网络异常 %s", e.__str__())
            raise e
        except Exception as e:
            logging.error("未知异常 %s", e.__str__())
            raise e

        self.checkStatus(result)
        logging.debug("get %s  %s",self.getSeatEndTimeWithSeatId,result['data']['endTimes'])
        return result['data']['endTimes']
    
    def reserveSeat(self,seatId,startTime = 480,endTime = 1320 ,layoutDate = None,tuesdayType=False):
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
            Returns:
            时间序列 [{'id': '420', 'value': '07:00'}]等，如果为空，则当天无法预定

        """
        if layoutDate == None:
            layoutDate = str((datetime.today() + timedelta(days=1)).date())
        result = None
        # 判断周二策略
        if datetime(*[int(x) for x in layoutDate.split('-')]).weekday() == 1:
            if tuesdayType == True: #执行上午策略
                if startTime < 720 and endTime > 720:
                    endTime = 720
    

        


if __name__ == "__main__":
    p = SeatClient.NewClient("220151214023", "316781")
    p.getReservations()
    p.getSeatStartTimeWithSeatId(8053)
    p.getSeatEndTimeWithSeatId(8053, 500)
