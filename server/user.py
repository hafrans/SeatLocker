
from flask_restful import Resource

import sys
sys.path.append("..")
from seat.__future__ import *
from flask import session,jsonify,g
from flask_restful import reqparse
from flask_restful import request,inputs
from .utils import *
from .error import *
import json
from datetime import datetime


class User(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', required=True,type=int, help='用户名不合法')
        self.parser.add_argument('password', required=True,type=str,help="密码不合法")
        self.parser.add_argument('schoolid',required=True,type=int,help="校区不合法")
        
    
    def get(self):
        if session.get("entity",None) == None:
            return returnData(ERR_LOGIN,'not login',"用户未登录",None)
        else:
            _meta = json.loads(session.get('entity',None))
            return returnData(OK,'success','已在登录状态',{'username':_meta['profile']['username'],'campus':_meta['campus'],'islogin':_meta['isLogin'],'id':_meta['id']})
    
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
                
                _id = result[0]
                p.id = _id
                print(datetime.today() - datetime.fromisoformat(result['register_time']))
                if result['password'] != password:
                    cu.execute("update users set password = ?", (password,))
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
        except UserCredentialError as err:
            return returnData(ERR_LOGIN,'failed',str(err),None)
        except Exception as err:
            return returnData(46001,'failed',str(err),None)
        finally:
            if cu != None:
               cu.close() 
        

        
        return returnData(OK,"success",'登录成功',args)