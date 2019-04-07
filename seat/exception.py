
"""
    All Exceptions Are Here.
"""



class NetWorkException(Exception):
    pass


class SystemMaintenanceError(Exception):
    pass


class SeatNotFoundException(Exception):
    pass

class RoomNotFoundException(Exception):
    pass


class UserCredentialError(Exception):
    GENERAL_ERROR = 1
    TOKEN_EXPIRED = 2
    USER_LOCKED   = 3
    def __init__(self,message,type = GENERAL_ERROR):
        self.type = type
        self.message = message
        super().__init__(message)
    
    def __eq__(self,type):
        return self.type == type
    def getType(self):
        return self.type
    def __str__(self):
        return "UserCredentialError: {0}, {1}".format(self.message,'用户或密码有误' if self.type == UserCredentialError.GENERAL_ERROR else '令牌失效')
    pass


class SeatReservationException(Exception):

    #预约时段不合法
    TIME_SPAN_ERROR = 0
    #已经有一个预约了 
    HAVE_RESERVED = 1 
   
    FAILED_RESERVED = 2  # 位置被抢
    # 无可用预约 
    NO_AVAILABLE_RESERVATIONS = 3 
    # 该IP不允许操作
    IP_NOT_ALLOWED = 4 
    #无效预约
    RESERVE_CANCEL_INVALIDED = 5 
    #预约重复取消
    RESERVE_HAVE_CANCELED = 6 

    #预约重复签到
    RESERVE_HAVE_CHECKEDIN = 8

    #不在可预约时间
    NOT_IN_RESERVE_TIME = 7


    #许可证已过期
    LICENSE_EXPIRED = 100

    def __init__(self,message,type = TIME_SPAN_ERROR):
        self.type = type
        self.message = message
        super().__init__(message)
    
    def __eq__(self,type):
        return self.type == type
    
    def getType(self):
        return self.type
    def __str__(self):
        return "SeatServationExcetion: {0}, {1}".format(self.message,self.type)
    
