"""
 Seat.ujn.edu.cn

 虚拟客户端

 @author Tensor Flower <3389@protonmail.ch>
 @copy right 2009 - 2018

"""

import urllib.request
import urllib.parse
import urllib.error
import json
import sys
import threading
import http.cookiejar
from datetime import date, timedelta, datetime, time as stime


def log(entity, text):
    print(datetime.today(), "线程：", threading.current_thread().getName(),
          "用户：", entity.user_config['username'], " ", text)


class SeatUtility(object):
    """
      seat lock class

    """
    __slots__ = "commands", "user_config", "base_url", "auth_url", "token", "islogin", "err_msg", "phone", "opener", "scookie"

    headers = {
        # "Host": "seat.ujn.edu.cn",
        "Connection": "Keep-Alive",
        "User-Agent": "",
        "X-Forwarded-For": "10.167.149.241"
    }
    cookie = None

    def __init__(self, profile, phone=None, head_url="http://seat.ujn.edu.cn"):
        # self.scookie = http.cookiejar.MozillaCookieJar(filename="./"+profile['username']+"_cookie.dat")
        # self.scookie.save()
        # self.scookie.load(ignore_discard=True)
        # parser = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener()
        # if os.path.exists("./"+profile['username']+".dat"):
        self.user_config = profile
        self.base_url = head_url + "/rest/v2"
        self.auth_url = head_url + "/rest/auth"
        self.token = ""
        self.phone = phone
        self.islogin = False
        SeatUtility.headers['Host'] = urllib.parse.urlparse(head_url).netloc
        self.err_msg = ""

    def _merge(self, data):
        if self.token is not None and len(self.token) > 0:
            data['token'] = self.token
            SeatUtility.headers['token'] = self.token
            return data
        else:
            raise Exception(datetime.today(),
                            "can not find a valid token while")

    def login(self):
        """
        用户登录
        :return:
        """
        request = urllib.request.Request(
            self.auth_url + "?" + urllib.parse.urlencode(self.user_config, encoding="UTF-8"))
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length") != "0":
            # self.scookie.save()
            data = json.load(result)
            if data['status'] == "success":
                print(datetime.today(), "登录成功！", "用户：",
                      self.user_config['username'], "token:", data['data']['token'])
                self.token = data['data']['token']
                self.islogin = True
                return False
            else:
                # {'status': 'fail', 'code': '13', 'message': '登录失败: 密码不正确', 'data': None}
                self.err_msg = data['message']
                if data['message'] == "System Maintenance":
                    self.err_msg == "维护"
                    return True
        else:
            self.err_msg = "网络异常"
        return False

    def fetch_booked_seat(self):
        pass

    def get_reserved_seats(self):
        """
        获取当前已预订的信息
        :return: Unit
        """
        request = urllib.request.Request(
            self.base_url + "/user/reservations" + "?" + urllib.parse.urlencode(self._merge({}), encoding="UTF-8"))
        result = self.opener.open(request)
        if result.status == 200 and result.getheader("Content-Length", 10) != "0":
            data = json.load(result)
            if data['status'] != "success":
                raise Exception("status is failed.")
            str = """
              使用中的位置：{0}
              状态：{1}，日期：{2}，
              开始：{3}，结束：{4}，
            """
            if data['data'] == None:
                print("当前未有预约")
                return False
            else:
                print(str.format(data['data'][0]['location'], data['status'], data['data'][0]['onDate'],
                                 data['data'][0]['begin'], data['data'][0]['end']))
                return data['data']

    def get_book_date_filters(self):
        """
        获取可预约时间的列表
        :return: list 可预约时间fmt:2018-03-12
        """

        """
            {
                "status": "success",
                "data": {
                    "buildings": [
                        [1, "东校区", 5],
                        [2, "主校区", 8]
                    ],
                    "rooms": [
                        [8, "第五阅览室北区", 2, 6],
                        [9, "第八阅览室北区", 2, 6],
                        [11, "第二阅览室北区", 2, 3],
                        [12, "第二阅览室中区", 2, 3],
                        [13, "第二阅览室南区", 2, 3],
                        [14, "第十一阅览室北区", 2, 3],
                        [15, "第十一阅览室中区", 2, 3],
                        [16, "第十一阅览室南区", 2, 3],
                        [17, "第三阅览室北区", 2, 4],
                        [18, "第三阅览室中区", 2, 4],
                        [19, "第三阅览室南区", 2, 4],
                        [21, "第十阅览室中区", 2, 4],
                        [22, "第十阅览室南区", 2, 4],
                        [23, "第六阅览室北区", 2, 7],
                        [24, "第六阅览室中区", 2, 7],
                        [25, "第六阅览室南区", 2, 7],
                        [27, "第七阅览室中区", 2, 7],
                        [28, "第七阅览室南区", 2, 7],
                        [31, "第四阅览室北区", 2, 5],
                        [32, "第四阅览室中区", 2, 5],
                        [33, "第四阅览室南区", 2, 5],
                        [34, "第九阅览室北区", 2, 5],
                        [35, "第九阅览室中区", 2, 5],
                        [36, "第九阅览室南区", 2, 5],
                        [37, "第五阅览室南区", 2, 6],
                        [38, "第五阅览室中区", 2, 6],
                        [40, "第八阅览室南区", 2, 6],
                        [41, "第一阅览室", 2, 2],
                        [46, "第七阅览室北区", 2, 7],
                        [47, "第八阅览室中区", 2, 6],
                        [49, "商科特色阅览室（诺奖图书 五楼南）", 1, 5],
                        [51, "第一期刊阅览室（现刊 四楼北）", 1, 4],
                        [52, "商科专业书库（二楼南）", 1, 2],
                        [53, "外文、工具书库（二楼北）", 1, 2],
                        [54, "二楼大厅", 1, 2],
                        [55, "人文书库（三楼南）", 1, 3],
                        [56, "综合书库（三楼北）", 1, 3],
                        [57, "第二期刊阅览室（过刊 四楼南）", 1, 4],
                        [58, "第三期刊阅览室（赠刊 五楼北）", 1, 5],
                        [59, "五楼走廊", 1, 5],
                        [60, "信息共享空间（一楼南）", 1, 1],
                        [62, "文化展厅（一楼北）", 1, 1]
                    ],
                    "hours": 15,
                    "dates": ["2018-03-11", "2018-03-12"]
                },
                "message": "",
                "code": "0"
            }
        """
        request = urllib.request.Request(
            url=self.base_url + "/free/filters?token=" + self.token)
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length") != "0":
            data = json.load(result)
            if data['status'] == 'success':
                return data['data']['dates']
            else:
                self.err_msg = data['message']
        else:
            self.err_msg = "网络异常"
        return False

    def get_free_room_list(self, schoolid=2):
        """
        获取空闲信息以及可预订时间
        :param schoolid: 校区id，1：东校区，2：西校区
        :return:
        """
        """
              {
                    "status": "success",
                    "data": [{
                        "roomId": 60,
                        "room": "信息共享空间（一楼南）",
                        "floor": 1,
                        "reserved": 0,
                        "inUse": 28,
                        "away": 0,
                        "totalSeats": 85,
                        "free": 57
                    }, {
                        "roomId": 62,
                        "room": "文化展厅（一楼北）",
                        "floor": 1,
                        "reserved": 0,
                        "inUse": 0,
                        "away": 0,
                        "totalSeats": 200,
                        "free": 200
                    }, {
                        "roomId": 54,
                        "room": "二楼大厅",
                        "floor": 2,
                        "reserved": 0,
                        "inUse": 0,
                        "away": 0,
                        "totalSeats": 29,
                        "free": 29
                    }, {
                        "roomId": 52,
                        "room": "商科专业书库（二楼南）",
                        "floor": 2,
                        "reserved": 0,
                        "inUse": 0,
                        "away": 0,
                        "totalSeats": 60,
                        "free": 60
                    }, {
                        "roomId": 53,
                        "room": "外文、工具书库（二楼北）",
                        "floor": 2,
                        "reserved": 0,
                        "inUse": 0,
                        "away": 0,
                        "totalSeats": 73,
                        "free": 73
                    }, {
                        "roomId": 55,
                        "room": "人文书库（三楼南）",
                        "floor": 3,
                        "reserved": 0,
                        "inUse": 1,
                        "away": 0,
                        "totalSeats": 57,
                        "free": 56
                    }, {
                        "roomId": 56,
                        "room": "综合书库（三楼北）",
                        "floor": 3,
                        "reserved": 0,
                        "inUse": 4,
                        "away": 0,
                        "totalSeats": 101,
                        "free": 97
                    }, {
                        "roomId": 51,
                        "room": "第一期刊阅览室（现刊 四楼北）",
                        "floor": 4,
                        "reserved": 0,
                        "inUse": 1,
                        "away": 0,
                        "totalSeats": 195,
                        "free": 194
                    }, {
                        "roomId": 57,
                        "room": "第二期刊阅览室（过刊 四楼南）",
                        "floor": 4,
                        "reserved": 0,
                        "inUse": 14,
                        "away": 0,
                        "totalSeats": 194,
                        "free": 180
                    }, {
                        "roomId": 59,
                        "room": "五楼走廊",
                        "floor": 5,
                        "reserved": 0,
                        "inUse": 0,
                        "away": 0,
                        "totalSeats": 34,
                        "free": 34
                    }, {
                        "roomId": 49,
                        "room": "商科特色阅览室（诺奖图书 五楼南）",
                        "floor": 5,
                        "reserved": 0,
                        "inUse": 3,
                        "away": 0,
                        "totalSeats": 212,
                        "free": 209
                    }, {
                        "roomId": 58,
                        "room": "第三期刊阅览室（赠刊 五楼北）",
                        "floor": 5,
                        "reserved": 0,
                        "inUse": 2,
                        "away": 0,
                        "totalSeats": 104,
                        "free": 102
                    }],
                    "message": "",
                    "code": "0"
                }

        :return:
        """
        request = urllib.request.Request(
            self.base_url + "/room/stats2/" + str(schoolid) + "?" + urllib.parse.urlencode(self._merge({}),
                                                                                           encoding="UTF-8"))
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length", 10) != "0":
            data = json.load(result)
            if data['status'] == 'success':
                return data['data']
            else:
                self.err_msg = data['message']
                return False
        else:
            self.err_msg = "网络异常"
        return False

    def get_room_seats_list(self, room_id=23, s_date=None):
        """
        获取房间内座位信息
        :param room_id: 房间id
        :param s_date: 预订时间；fmt:'2018-01-01'
        :return:
        """
        if s_date is None:
            s_date = (datetime.today() + timedelta(days=1)).date().__str__()
        request = urllib.request.Request(
            self.base_url + "/room/layoutByDate/" + str(room_id) + "/" + s_date.__str__() + "?token=" + self.token)
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length", 10) != "0":
            data = json.load(result)
            if data['status'] == 'success':
                return [x for x in data['data']['layout'].values() if "id" in x and "type" in x]
            else:
                self.err_msg = data
                return False
        else:
            self.err_msg = "网络异常"
            return False

    def get_start_times(self, seat_id=8053, s_date=None):
        """
        获取座位的可开始预约时间
        :param seat_id: 座位id
        :param s_date: 预约时间
        :return:
        """
        if s_date is None:
            s_date = (datetime.today() + timedelta(days=1)).date().__str__()
        request = urllib.request.Request(
            self.base_url + "/startTimesForSeat/" + str(seat_id) + "/" + s_date.__str__() + "?token=" + self.token)
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length") != "0":
            data = json.load(result)
            if data['status'] == 'success':
                startTimes = data['data']['startTimes']
                return sorted([x['id'] for x in startTimes])
            else:
                self.err_msg = data['message']
        else:
            self.err_msg = "网络异常"
        return False

    def get_end_times(self, seat_id=8053, start_times=480, s_date=None):
        """
        获取座位的结束时间
        :param seat_id: 座位id
        :param start_times: 座位开始时间
        :param s_date: 预订日期，默认是今天的下一天（明天）
        :return:
        """
        if s_date == None:
            s_date = (datetime.today() + timedelta(days=1)).date().__str__()
        request = urllib.request.Request(
            self.base_url + "/endTimesForSeat/" + str(seat_id) + "/" + s_date.__str__() + "/" + str(
                start_times) + "?token=" + self.token)
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length") != "0":
            data = json.load(result)
            if data['status'] == 'success':
                startTimes = data['data']['endTimes']
                # for k in startTimes:
                #     print(k['id'], k['value'])
                return sorted([x['id'] for x in startTimes], reverse=True)
            else:
                self.err_msg = data['message']
        else:
            self.err_msg = "网络异常"
        return False

    def book_seat(self, seat_id=8053, s_date=None, start_time=480, end_time=1320):
        """
        预订位置
        :param seat_id:座位id
        :param s_date: 预订日期，默认为明天
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return:
        """
        if s_date is None:
            s_date = (datetime.today() + timedelta(days=1)).date().__str__()
        # 周二最多到12：00，下午闭馆
        if start_time < 720 and datetime(*[int(x) for x in s_date.split("-")]).date().weekday() == 1:
            end_time = 720  # 最多约到12：00
        # 12-16
        if start_time >= 720 and end_time <= 960 and datetime(*[int(x) for x in s_date.split("-")]).date().weekday() == 1:
            return None
        print(datetime.today(), "线程：【", threading.current_thread().getName(), "】", "用户：", self.user_config['username'],
              "开始预订日期为", s_date, "座位id为", seat_id, "时间为：", start_time/60, "-", end_time/60, "的座位", file=sys.stderr)
        postForm = {
            'token': self.token,
            'startTime': start_time,
            'endTime': end_time,
            'seat': seat_id,
            'date': s_date
        }
        request = urllib.request.Request(self.base_url + "/freeBook",
                                         data=bytes(urllib.parse.urlencode(postForm, encoding="UTF-8"),
                                                    encoding='UTF-8'))
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        # self.scookie.save()
        if result.status == 200 and result.getheader("Content-Length") != "0":
            data = json.load(result)
            if data['status'] == 'success':
                """
                 {
                        "status": "success",
                        "data": {
                            "id": 3707691,
                            "receipt": "4028-691-6",
                            "onDate": "2018 年 03 月 10 日",
                            "begin": "08 : 00",
                            "end": "09 : 00",
                            "location": "主校区7层703室区第六阅览室北区，座位号049",
                            "checkedIn": false
                        },
                        "message": "",
                        "code": "0"
                    }

                    {'status': 'fail', 
                    'data': None, 
                    'message': '预约失败，请尽快选择其他时段或座位', 
                    'code': '1'}
                """
                str = """
                预定成功：
                id : {0} ,
                日期：{1},
                开始：{2}，结束{3}，
                位置：{4}
                """
                print(str.format(data['data']['id'], data['data']['onDate'], data['data']['begin'], data['data']['end'],
                                 data['data']['location']))
                return data['data']
            else:
                self.err_msg = data['message']
                return False
        else:
            self.err_msg = "网络异常"
            return False

    def get_last_error(self):
        return self.err_msg

    def library_check_in(self):
        request = urllib.request.Request(
            self.base_url + "/checkIn?token=" + self.token, headers=SeatUtility.headers)
        try:
            result = self.opener.open(request)
        except Exception as e:
            self.err_msg = e.__str__()
            return False
        if result.status == 200 and result.getheader("Content-Length") != 0:
            print(bytes.decode(result.read()))
        else:
            print("False")
        """
            {"status":"success","data":{"id":5977245,"receipt":"4023-245-5","onDate":"2019 年 03 月 22 日","begin":"19 : 55","end":"20 : 55","location":"西校区3层303室区第二阅览室中区，座位号209"},"message":"成功登记入场","code":"0"}
        """
