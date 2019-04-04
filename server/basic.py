import sys
sys.path.append("..")
import json
from .error import *
from .utils import *
from flask_restful import reqparse
from flask_restplus import Resource
from flask import session, jsonify, g
from datetime import datetime
from seat.__future__ import *




class Room(Resource):
    """
        FetchAll Room status
    """

    def __init__(self,api):
        pass

    def get(self):
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            p = SeatClient.deserialize(session.get('entity'))
            result = p.getRoomStatus()
            return returnData(OK, 'success', "ok", result)

class AvailableDates(Resource):
    def __init__(self,api):
         pass

    def get(self):
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                result = p.getReservationAvailableDates()
                return returnData(OK, 'success', "ok", result)
            except UserCredentialError as err:
                if err == UserCredentialError.TOKEN_EXPIRED:
                    invalidate(session)
                    return returnData(ERR_LOGIN, 'not login', "令牌失效", None)
                else:
                    return returnData(ERR_LOGIN, 'not login', "其他原因({0})".format(err.type), None)
            except NetWorkException as err:
                invalidate(session)
                return returnData(500,'failed',"目标服务器主机繁忙，请稍后再试",None)
            except SystemMaintenanceError as err:
                return returnData(501,'failed',"服务器正在维护中，请稍后再试",None)
            except Exception as err:
                raise err



class Book(Resource):
    """
        get start end end time of one seat.
        /0000-00-00/1234/2314/[start,end]/[0,starttime(480)]

        reserve seat with seatId,roomId,date,start,end,tuesday
    """

    def __init__(self,api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "seatId", type=int, help="请输入正确的座位ID", required=True)
        self.parser.add_argument(
            "roomId", type=int, help="请输入正确的房间ID", required=True)
        self.parser.add_argument("date", type=str,
                                 help="请输入正确的日期", required=True)
        self.parser.add_argument(
            "start", type=int, help="请输入开始时间", required=True)
        self.parser.add_argument(
            "end", type=int, help="请输入结束时间", required=True)
        self.parser.add_argument(
            "tuesday", type=int, help="请输入正确的标志", required=True)
        pass

    def get(self, date, roomId, seatId, action, arg):
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                if date != None:
                    datetime.fromisoformat(date)  # 故意引发错误ValueError
                p = SeatClient.deserialize(session.get('entity'))
                if action == "start" and seatId != None:
                    result = p.getSeatStartTimeWithSeatId(
                        seatId, layoutDate=date)
                    return returnData(OK, 'success', "start", result)
                elif action == "end" and arg != None: ## bugfix 支持now
                    result = p.getSeatEndTimeWithSeatId(
                        seatId, arg, layoutDate=date)
                    return returnData(OK, 'success', "end", result)
                else:
                    return returnData(FAILED, 'something not specified', "指令不完整", None)

            except UserCredentialError as err:
                if err == UserCredentialError.TOKEN_EXPIRED:
                    invalidate(session)
                    return returnData(ERR_LOGIN, 'not login', "令牌失效", None)
                else:
                    return returnData(ERR_LOGIN, 'not login', "其他原因({0})".format(err.type), None)
            except ValueError as err:
                return returnData(FAILED, 'failed', "日期格式不合法", None)
            except NetWorkException as err:
                invalidate(session)
                return returnData(500,'failed',"目标服务器主机繁忙，请稍后再试",None)
            except SystemMaintenanceError as err:
                return returnData(501,'failed',"服务器正在维护中，请稍后再试",None)
            except Exception as err:
                raise err

    def post(self):
        args = self.parser.parse_args()
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                cursor = g.db.cursor()
                datetime.fromisoformat(args['date']) #主动试错
                p = SeatClient.deserialize(session.get('entity'))
                result = p.reserveSeat(args['seatId'],startTime=args['start'],endTime=args['end'],layoutDate=args['date'],tuesdayType=True if args['tuesday'] == 1 else False)
                ##用于座位缓存
                cursor.execute("insert into seatinfo (id,room,location,schoolid,school )values (?,?,?,?,?,?)",(args['seatId'],args['roomId'],result['location'],p.opener.region['id'],p.school))
                g.db.commit()
                ## 缓存结束
                return returnData(OK, 'success', "预约成功！", None)
            except SeatReservationException as err:
                if err == SeatReservationException.NO_AVAILABLE_RESERVATIONS:
                    return returnData(FAILED, 'failed', '没有可取消的预约', None)
                if err == SeatReservationException.TIME_SPAN_ERROR:
                    return returnData(FAILED, 'failed', '您预约的时间段不合法', None)
                if err == SeatReservationException.HAVE_RESERVED:
                    return returnData(FAILED, 'failed', '您已经有一个有效预约了', None)
                if err == SeatReservationException.FAILED_RESERVED:
                    return returnData(FAILED, 'failed', '您选择的位置被其他人占用，请尽快选择其他时段或座位', None)
                if err == SeatReservationException.NOT_IN_RESERVE_TIME:
                    return returnData(FAILED, 'failed', '目前不在选座时间段内，请使用选座助手,自动帮您预约座位', None)
                if err == SeatReservationException.LICENSE_EXPIRED:
                    return returnData(FAILED, 'failed', '出现了不可抗因素：图书馆座位预约系统许可证过期', None)
            except ValueError as err:
                return returnData(FAILED, 'failed', "日期格式不合法", None)
            except Exception as err:
                raise err
            finally:
                cursor.close() 
        pass

    pass


class Other(Resource):
    pass


class Seats(Resource):

    def __init__(self,api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("room", type=int, help="请输入正确的room ID")
        pass

    def get(self, roomId):
        if roomId == None:
            return returnData(FAILED, 'roomId is empty', "ROOMID 不正确，判定非正常访问", None)
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                result = p.getSeatsInRoomWithRoomId(roomId)
                _result = []
                for i in result['layout'].values():
                    if i['type'] == 'seat':
                        _result.append(i)
                return returnData(OK, 'success', "success", _result)
            except Exception as err:
                raise err


class RemoteAffairs(Resource):
    pass


class History(Resource):
    def __init__(self,api):
        pass

    def get(self):
        """
            获取
        """
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                result = p.getHistory()
                return returnData(OK, 'success', "已终止使用当前预约", result)
            except SeatReservationException as err:
                if err == SeatReservationException.NO_AVAILABLE_RESERVATIONS:
                    return returnData(FAILED, 'failed', '没有可取消的预约', None)
            except Exception as err:
                raise err


class Checkin(Resource):
    def __init__(self,api):
        pass

    def get(self):
        """
            预约
        """
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                cursor = g.db.cursor()
                p = SeatClient.deserialize(session.get('entity'))
                if not CAMPUS_CHECKIN_ENABLED(p.campus):
                     return returnData(ERR_NO_ACCESS, 'failed', '您的校区暂未开通校外签到功能', None)
                
                result = cursor.execute(
                    "select checkin from settings where user = ? ", (p.id,)).fetchone()
                if result == None:
                    raise Exception("数据错误")
                if result[0] == -2:
                    return returnData(ERR_NO_ACCESS, 'failed', '您没有使用该功能的权限', None)
                if result[0] > -1:  # -1是无限使用
                    if result[0] == 0:
                        return returnData(ERR_EXHAUST, 'success', '您的使用次数已消耗完毕，请充值', None)
                g.db.commit()
                _result = None
                _resv = p.getReservations()  # 先获取可不可以签到
                if len(_resv) == 0:
                    return returnData(FAILED, 'failed', '没有预约的项目，不需要签到', _result)
                if _resv[0]['status'] == "RESERVE":
                    _result = p.checkIn()
                else:
                    return returnData(OK_NOT_REPEAT, 'success', '已入场,无需重新签到', _result)
                if session.get('_resv',None) != _resv[0]['receipt']:
                    # 录入信息
                    cursor.execute("insert into log (user,jigann,content) values (?,?,?)", (p.id, str(
                        datetime.today().replace(microsecond=0)), "签到成功"))
                    cursor.execute(
                        "update settings set checkin = ? where user = ? ", (result[0]-1, p.id,))
                    g.db.commit()
                    session['_resv'] =  _resv[0]['receipt']
                    return returnData(OK, 'success', '成功登记入场', _result)
                else:
                    return returnData(OK, 'success', '成功登记入场,但约座系统不显示正在履约，已经为您重新登记，此次不消耗签到次数，您可以稍后刷新后再查看签到状态', _result)
            except SeatReservationException as e:
                if e == SeatReservationException.NO_AVAILABLE_RESERVATIONS:
                    # cursor.execute("insert into log (user,jigann,content) values (?,?,?)", (p.id, str(
                    #     datetime.today().replace(microsecond=0)), "签到成功"))
                    return returnData(FAILED, 'failed', '没有可用预约,或签到不在时间段内', None)
                elif e == SeatReservationException.RESERVE_HAVE_CHECKEDIN:
                    return returnData(FAILED, 'failed', '已成功登记入场,无需重复签到', None)
            except Exception as err:
                raise err
            finally:
                g.db.commit()
                cursor.close()

    def delete(self):
        """
            停止使用
        """
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                if p.stop():
                    return returnData(OK, 'success', "已终止使用当前预约", None)
            except SeatReservationException as err:
                if err == SeatReservationException.NO_AVAILABLE_RESERVATIONS:
                    return returnData(FAILED, 'failed', '没有可取消的预约', None)
            except Exception as err:
                raise err


class Reservation(Resource):

    def __init__(self,api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "id", type=int, required=True, help="请输入正确的id，不是入侵？")

    def get(self):
        """
        获取预约
        成功：
        {'id': 6013511, 
        'receipt': '4023-511-2',
         'onDate': '2019-03-26', 
         'seatId': 20184, 
         'status': 'CHECK_IN',
          'location': '西校区3层303室区第二阅览室北区，
          座位号112', 'begin': '16:13', 'end': '17:13',
           'actualBegin': '16:14', 'awayBegin': None, 'awayEnd': None, 
           'userEnded': False, 'message': ''}
        """
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                result = p.getReservations()
                if len(result) == 0:
                    return returnData(DATA_EMPTY, 'success', '暂时没有今日预约', None)
                return returnData(OK, 'success', 'none', result[0])
            except SeatReservationException as err:
                if err == SeatReservationException.RESERVE_CANCEL_INVALIDED:
                    return returnData(FAILED, 'failed', "无效预约", None)
                elif err == SeatReservationException.RESERVE_HAVE_CANCELED:
                    return returnData(FAILED, 'failed', "预约已被取消，不可重复取消", None)
            except Exception as err:
                raise err

    def post(self):
        pass

    def delete(self):
        """
            取消预约
        """
        args = self.parser.parse_args()
        if session.get("entity", None) == None:
            return returnData(ERR_LOGIN, 'not login', "用户未登录", None)
        else:
            try:
                p = SeatClient.deserialize(session.get('entity'))
                if p.cancel(args['id']) == True:
                    return returnData(OK, 'success', '预约取消成功', None)
            except SeatReservationException as err:
                if err == SeatReservationException.RESERVE_CANCEL_INVALIDED:
                    return returnData(FAILED, 'failed', "无效预约", None)
                elif err == SeatReservationException.RESERVE_HAVE_CANCELED:
                    return returnData(FAILED, 'failed', "预约已被取消，不可重复取消", None)
            except Exception as err:
                raise err
