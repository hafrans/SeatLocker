
from flask_restful import Resource

import sys
sys.path.append("..")
from seat.__future__ import *
from flask import session,jsonify,g
from flask_restful import reqparse
from flask_restful import request
from .utils import returnData
from .error import *


class User(Resource):

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', required=True,type=int, help='用户名不合法')
        self.parser.add_argument('password', required=True,type=int,help="密码不合法")
        self.parser.add_argument('schoolid',required=True,type=int,help="校区不合法")
        
    
    def get(self):
        pass
    
    def post(self):
        sch = None
        args = self.parser.parse_args()
        if args['schoolid'] not in [1,2]:
            return returnData(BAD_SCHOOL_ID,"请检查学校ID是否正确",None)
        if args['schoolid'] == 1:
            sch = EAST_CAMPUS
        else:
            sch = WEST_CAMPUS
        
        return returnData(0,"success",args)