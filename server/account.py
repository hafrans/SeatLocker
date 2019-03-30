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



class User(Resource):

    def __init__(self,api):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', required=True,type=int, help='用户名不合法')
        self.parser.add_argument('password', required=True,type=str,help="密码不合法")
        self.parser.add_argument('schoolid',required=True,type=int,help="校区不合法")
        
    
    def get(self):
        simpleCheckLogin(session)
        p = SeatClient.deserialize(session.get('entity'))
        p.getReservations() #检查与服务器的连接性
        _meta = json.loads(session.get('entity',None))
        cursor = g.db.cursor()
        result = cursor.execute("select * from settings where user = ? ",(_meta['id'],)).fetchone()
        cursor.close()
        return returnData(OK,'success','已在登录状态',{'username':_meta['profile']['username'],'campus':_meta['campus'],'islogin':_meta['isLogin'],'id':_meta['id'],'checkin':result['checkin'],'reserve':result['reserve']})
           
            
    def delete(self):
        if session.get("entity",None) == None:
            return returnData(ERR_LOGIN,'not login',"用户未登录",None)
        else:
            session['entity'] = None
            return returnData(OK,'success',"注销成功",None)

    def post(self):
        sch = None
        args = self.parser.parse_args()
        username = str(args['username'])
        password = str(args['password'])
        current_time = str(parseDate(datetime.today()))
        if args['schoolid'] not in [1,2]:
            return returnData(BAD_SCHOOL_ID,'failed',"请检查学校ID是否正确",None)
        if args['schoolid'] == 1:
            sch = EAST_CAMPUS
        else:
            sch = WEST_CAMPUS
        cu = None
        try:
            p = SeatClient.NewClient(str(args['username']),str(args['password']),sch)
            if p:
                #判断用户在不在库
                cu = g.db.cursor()
                _id = None
                result = cu.execute("select * from users where username = ? ",
                                   ( username, ) ).fetchone()
                g.db.commit()
                if result == None:
                    cu.execute("insert into users (username,password,token,register_time) values (?,?,?,?)",
                              ( username,password,p.token,current_time) )
                    g.db.commit()
                    if cu.rowcount == 0:
                        raise Exception("Can not insert into db")
                    else:
                        result = cu.execute("select * from users where username = ? ",( username,)).fetchone()
                        #写入setting表
                        cu.execute("insert into settings (user) values (?)",(result[0],) )
                        g.db.commit()
                        if cu.rowcount == 0:
                            raise Exception("Can not insert into db")
                
                _id = result[0]
                p.id = _id
                if result['password'] != password:
                    cu.execute("update users set password = ? where id = ?", (password,_id))
                    cu.execute("insert into log (user,jigann,content) values (?,?,?)",(_id,current_time,"修改了密码"))
                if result['lock'] == 1:
                    cu.execute("insert into log (user,jigann,content) values (?,?,?)",(_id,current_time,"用户被系统锁定，并尝试登录"))
                    g.db.commit() 
                    raise UserCredentialError("用户被本系统锁定，请联系管理员！",UserCredentialError.GENERAL_ERROR)   
                #update log
                cu.execute("insert into log (user,jigann,content) values (?,?,?)",(_id,current_time,"成功登录"))
                g.db.commit()        
                session['entity'] = p.serialize()
                return returnData(OK,'success','登录成功',None)
        except Exception as err:
            raise err
        finally:
            if cu != None:
               cu.close() 

