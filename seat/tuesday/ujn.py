import sys
import logging
sys.path.append("../../")
from seat.exception import *
from datetime import datetime

def ujn(layoutDate,startTime,endTime,tuesdayType=False):
    if datetime(*[int(x) for x in layoutDate.split('-')]).weekday() == 1:
            if startTime >= 720 and endTime <= 960:
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
        raise SeatReservationException("初始结束时间不合法！",SeatReservationException.TIME_SPAN_ERROR)
    return startTime,endTime