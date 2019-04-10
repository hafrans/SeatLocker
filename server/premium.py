from seat.__future__ import *
from datetime import datetime,timedelta
from flask import session, jsonify, g
from flask_restplus import Resource
from flask_restful import reqparse
from .utils import *
from .error import *
import json
import sys
import time
sys.path.append("..")


PREMIUM_SEATS = 10
PREMIUM_DATES = 0

PREMIUM_CHECKIN = 1
PREMIUM_CHECKIN_AUTO = 2

PREMIUM_RESERVE_AUTO = 1


class AutoCheckIn(Resource):
    """
        设置自动签到

        !! 关于自动签到的识别FLAG == 1
    """

    def __init__(self, api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "action", type=int, help="请输入正确的参数！有攻击嫌疑。", required=True)

    def get(self):
        p = simpleCheckLogin(session)
        try:
            cursor = g.db.cursor()
            result = cursor.execute(
                "select * from settings where user = ?", (p.id,)).fetchone()
            if result == None:
                raise Exception("Data Base Error")
            return returnData(OK, "success", "获取成功", {'currentprice':PREMIUM_CHECKIN_AUTO,'result': result['checkin'], 'switch': result['auto_checkin'] == p.campus['id'],'support':CAMPUS_CHECKIN_ENABLED(p.campus)})
        except Exception as e:
            raise e
        finally:
            cursor.close()

    def post(self):
        p = simpleCheckLogin(session)
        args = self.parser.parse_args()
        cursor = g.db.cursor()
        try:
            result = cursor.execute(
                "select * from settings where user = ? ", (p.id,)).fetchone()
            if result == None:
                raise Exception("Data Base Error")
            """
             fetch result from database first.
            """
            if result['checkin'] == -2:
                return returnData(FAILED, "failed", "您暂无权限使用该项业务！", None)
            if result['checkin'] == 0:
                return returnData(FAILED, "failed", "您的使用次数已经使用完毕", None)
            if args['action'] == 0 and result['auto_checkin'] != 0: #是否可以关闭
                cursor.execute(
                    "update settings set auto_checkin = 0 where user = ? ", (p.id,))
                g.db.commit()
                return returnData(OK, "success", "设置成功！", None)
            if args['action'] == 1 and result['auto_checkin'] != p.campus['id']:#是否可以开启
                cursor.execute(
                    "update settings set auto_checkin = ? where user = ? ", (p.campus['id'],p.id,))
                g.db.commit()
                return returnData(OK, "success", "设置成功！", None)

            return returnData(OK, "success", "设置失败，设置未修改", None)

        finally:
            g.db.commit()
            cursor.close()
        pass

    def delete(self):
        pass
    def patch(self):
        p = simpleCheckLogin(session)
        cursor = g.db.cursor()
        try:
            result = cursor.execute(
                "select * from log where user = ?  and (type = 10 or type = 11) order  by jigann desc LIMIT 15", (p.id,)).fetchall()
            if result == None:
                raise Exception("Data Base Error")
            """
             fetch result from database first.
            """
            return returnData(OK, "success", "OK", [dict(x) for x in result])

        finally:
            g.db.commit()
            cursor.close()



class AutoReserve(Resource):

    def __init__(self, api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("id", type=int, help="Id 不正确！", required=True)
        self.parser_post = reqparse.RequestParser()
        self.parser_post.add_argument(
            "start", type=int, help="请输入开始时间", required=True)
        self.parser_post.add_argument(
            "end", type=int, help="请输入结束时间", required=True)
        self.parser_post.add_argument(
            "startdate", type=str, help="请输入开始日期", required=True)
        self.parser_post.add_argument(
            "enddate", type=str, help="请输入结束日期", required=False)
        self.parser_post.add_argument(
            "seat", type=int, help="请输入座位ID", required=True)
        self.parser_post.add_argument(
            "room", type=int, help="请输入房间ID", required=True)
        self.parser_post.add_argument(
            "tuesday", type=int, help="请输入周二策略", required=True)
        self.parser_post.add_argument(
            "priority", type=int, help="请输入优先级", required=True)
        ########################################
        self.parser2 = reqparse.RequestParser()
        self.parser2.add_argument(
            "action", type=int, help="请输入正确的参数！有攻击嫌疑。", required=True)

    def get(self):
        """
        获取状态+信息
        """
        p = simpleCheckLogin(session)
        cursor = g.db.cursor()
        try:
            settings = cursor.execute(
                "select * from settings where user = ? ", (p.id,)).fetchone()
            seats = cursor.execute(
                "select * from seat where user = ? order by priority desc , id asc", (p.id,)).fetchall()
            return returnData(OK, "success", "获取成功", {'config': {'reserve': settings['reserve'],'autoreserve':True if settings['auto_reserve'] else False, 'maximum': PREMIUM_SEATS}, 'seats': [dict(x) for x in seats]})
        finally:
            g.db.commit()
            cursor.close()
        pass
    
    def post(self):
        p = simpleCheckLogin(session)
        args = self.parser2.parse_args()
        cursor = g.db.cursor()
        try:
            result = cursor.execute(
                "select * from settings where user = ? ", (p.id,)).fetchone()
            if result == None:
                raise Exception("Data Base Error")
            """
             fetch result from database first.
            """
            if result['reserve'] == -2:
                return returnData(FAILED, "failed", "您暂无权限使用该项业务！", None)
            if result['reserve'] == 0:
                return returnData(FAILED, "failed", "您的使用次数已经使用完毕", None)
            if args['action'] == 0 and result['auto_reserve'] != 0: #是否可以关闭
                cursor.execute(
                    "update settings set auto_reserve = 0 where user = ? ", (p.id,))
                g.db.commit()
                return returnData(OK, "success", "设置成功！", None)
            if args['action'] == 1 and result['auto_reserve'] == 0:#是否可以开启
                cursor.execute(
                    "update settings set auto_reserve = 1 where user = ? ", (p.id,))
                g.db.commit()
                return returnData(OK, "success", "设置成功！", None)

            return returnData(OK, "success", "设置失败，设置未修改", None)

        finally:
            g.db.commit()
            cursor.close()
        pass


    def put(self):
        """
         新增
        """
        p = simpleCheckLogin(session)
        args = self.parser_post.parse_args()
        cursor = g.db.cursor()
        try:
            settings = cursor.execute(SQL_ONE_PERSON, (p.id,)).fetchone()
            if settings['reserve'] == -2:
                return returnData(FAILED, "failed", "您暂时没有权限使用该工具！", None)
            if settings['reserve'] == 0:
                return returnData(FAILED, "failed", "您的使用次数已经使用完", None)
            # 检测次数，如果大于阈值，则停止
            seatCount = cursor.execute(
                "select count(1) from seat where user = ? ", (p.id,)).fetchone()[0]
            if seatCount >= PREMIUM_SEATS:
                return returnData(FAILED, "failed", "以达到最大候选座位", None)
            # 深一步验证所有数据
            if args['start'] >= args['end'] or args['start'] > 1320 or args['start'] < 360 or args['end'] > 1320 or args['end'] < 360:
                return returnData(FAILED, "failed", "初始时间以及结束时间验证不合法", None)
            if args['enddate'] != None and (datetime.fromisoformat(args['startdate']) - datetime.fromisoformat(args['enddate'])).days > 0:
                return returnData(FAILED, "failed", "初始日期以及结束日期验证不合法", None)
            datetime.fromisoformat(args['startdate'])  # 主动触发报错

            # 检测是否被用,自己用的话会提示不可重复选座
            seats = cursor.execute(
                "select * from seat where seat = ? and (julianday('now') >= julianday(start_date) and julianday('now') <= julianday(end_date) or julianday('now') >= julianday(start_date) and end_date is null)", (args['seat'],)).fetchone()
            if seats != None:
                if seats['user'] == p.id:
                    return returnData(FAILED, "failed", "您申请为位置有重复", None)
                else:
                    return returnData(FAILED, "failed", "非常抱歉，有其他用户在此时段选择了该位置，时间是{0}-{1},您可以选择与其协商或者更换其他位置".format(seats['start_date'], "2099-12-31" if seats['end_date'] == None else seats['end_date']), {'user': seats['user'], 'id': seats['id']})

            # 获取座位信息，如果失败就从服务上获取一条，减少访问服务器的次数。
            _seatName = None
            _seatInfo = cursor.execute(
                "select name from seatinfo where id = ?", (args['seat'],)).fetchone()
            if _seatInfo == None:
                _seatName = p.getSeatRoomBundle(
                    args['room'], args['seat'], p.campus)
                #store in seatInfo
            else:
                _seatName = _seatInfo['name']
            cursor.execute(SQL_STORE_SEAT, (p.id, args['room'], args['seat'], _seatName, args['start'], args['end'], args['startdate'],
                                            args['enddate'], args['priority'], True if args['tuesday'] == 1 else False, datetime.today().date().__str__()))
            g.db.commit()
            return returnData(OK, "success", "添加成功", None)
        except ValueError as err:
            return returnData(FAILED, "failed", "日期格式有问题"+str(err), None)
        except Exception as err:
            raise err
        finally:
            g.db.commit()
            cursor.close()

    def delete(self):
        """
          删除
        """
        p = simpleCheckLogin(session)
        args = self.parser.parse_args()
        cursor = g.db.cursor()
        try:
            cursor.execute(
                "delete from seat where user = ? and id = ?", (p.id, args['id']))
            g.db.commit()
            if cursor.rowcount == 1:
                return returnData(OK, "success", "删除成功！", None)
            else:
                return returnData(FAILED, "failed", "删除失败", None)
        finally:
            g.db.commit()
            cursor.close()
        pass

    def patch(self):
        p = simpleCheckLogin(session)
        cursor = g.db.cursor()
        try:
            result = cursor.execute(
                "select * from log where user = ?  and (type = 20 or type = 21) order  by jigann desc LIMIT 15", (p.id,)).fetchall()
            if result == None:
                raise Exception("Data Base Error")
            """
             fetch result from database first.
            """
            return returnData(OK, "success", "OK", [dict(x) for x in result])

        finally:
            g.db.commit()
            cursor.close()



"""
template:
    def delete(self):
        
        
        p = simpleCheckLogin(session)
        cursor = g.db.cursor()
        try:
              
        finally:
            g.db.commit()
            cursor.close()
        pass
"""

class GiftCode(Resource):
    def __init__(self, api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("code",required=True,help="请填写GIFT CODE！",type=str)
    
    def post(self):
        #check freq
        args = self.parser.parse_args()
        lastTime = session.get("gift_time",0)
        if (int(time.time()) - int(lastTime) ) < 3:
            return returnData(FAILED,"failed",'您的动作太快，请稍后再试！',None)
        else:
            session['gift_time'] = int(time.time()) #设置时间
        p = simpleCheckLogin(session)
        #read code
        cursor = g.db.cursor()
        try:
            result = cursor.execute("select * from giftcode where code = ?",(args['code'],)).fetchone()
            if result == None:
                return returnData(FAILED,"failed",'GIFT CODE 无效',None)
            if result['remaining'] <= 0:
                return returnData(FAILED,"failed",'抱歉，GIFT CODE 名额已满，请换一个再试',None)
            _time_now = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
            _code_start = datetime.fromisoformat(result['startdate'])
            if _code_start > _time_now:
                return returnData(FAILED,"failed",'抱歉，GIFT CODE 未到放出时间',None)
            _code_end = datetime.fromisoformat(result['enddate'])
            if _code_end < _time_now:
                return returnData(FAILED,"failed",'抱歉，GIFT CODE 已过期',None)
            _lastlog = cursor.execute("select * from giftcode_log where code = ? and user = ? order by time desc limit 1",(args['code'],p.id,)).fetchone()
            if _lastlog != None:
                #转换成时间
                if result['cycle'] == 0:
                    return returnData(FAILED,"failed",'抱歉，该CODE已被您使用！',None)
                usetime = datetime.fromisoformat(_lastlog['time']) 
                if (datetime.today() - usetime + timedelta(hours=2)).days < result['cycle']:
                    return returnData(FAILED,"failed",'抱歉，您最近使用过这个CODE了，如果是周期性CODE，请等些时间再试！',None)
            _usersetting = cursor.execute("select * from settings where user = ?",(p.id,)).fetchone()
            _changed_checkin = _usersetting['checkin']
            _changed_reserve = _usersetting['reserve']
            #使用code
            with g.db:
                cursor.execute("insert into giftcode_log (user,code,time) values(?,?,?)",(p.id,args['code'],str(parseDate(datetime.today())),))
                cursor.execute("update giftcode set remaining = ? where code = ?",(result['remaining'] -1 ,args['code'],))
                if _usersetting['checkin'] >= 0:
                    _changed_checkin += result['checkin']
                if _usersetting['reserve'] >= 0:
                    _changed_reserve += result['reserve']
                if _usersetting['checkin'] == -2:
                    _changed_checkin = result['checkin']
                if _usersetting['reserve'] == -2:
                    _changed_reserve = result['reserve']
                if _usersetting['checkin'] == -1:
                    _changed_checkin = -1
                if _usersetting['reserve'] == -1:
                    _changed_reserve = -1
                cursor.execute("update settings set checkin = ?, reserve = ? where user = ? ",(_changed_checkin,_changed_reserve,p.id,))
            return returnData(OK,"success",'使用成功，增加签到点数{0}，预约点数{1}'.format(result['checkin'],result['reserve']),None)
        except Exception as e:
            raise e
        finally:
            cursor.close()
                



        
