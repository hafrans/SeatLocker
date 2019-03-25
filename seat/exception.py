
"""
    All Exceptions Are Here.
"""



class NetWorkException(Exception):
    pass


class SystemMaintenanceError(Exception):
    pass


class UserCredentialError(Exception):
    GENERAL_ERROR = 1
    TOKEN_EXPIRED = 2
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

    TIME_SPAN_ERROR = 0
    HAVE_RESERVED = 1
    FAILED_RESERVED = 2
    NO_AVAILABLE_RESERVATIONS = 3
    IP_NOT_ALLOWED = 4

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
    
