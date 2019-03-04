#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
   auto seat locker

   @author Tensor Flower <3389@protonmail.ch>
   @copy right 2009 - 2018

"""

import sys
import os.path
import threading
import time
import gc
from datetime import date, timedelta, datetime, time as stime
from seat.utility import SeatUtility, log


def thread_seat_lock(username, password, room_id=23, seat_id=8053, start_time=480, end_time=1320, date_time=None,handle=False):
    """

     创建任务 ，arguments 看参数名就懂。
     支持精确抢座，单区顺序抢座，优先列表抢座（Not Implemented yet.）

    :param username:
    :param password:
    :param room_id:
    :param seat_id:
    :param start_time:
    :param end_time:
    :param date_time:
    :return:
    """
    # 设置抢座的时间
    if date_time is None:
        tod = datetime.today()
        if tod.hour > 6:
            date_time = (tod + timedelta(days=2)).date().__str__()  # 后天的，因为明天已经开抢了
        else:
            date_time = (tod + timedelta(days=1)).date().__str__()  # 明天的，因为今天抢明天的
    person = SeatUtility({'username': username, 'password': password});

    while person.login():
        log(person,person.err_msg)
        time.sleep(5)
    
    if handle is not True: # 要等待到4点58左右执行
        d = datetime(*tuple(map(lambda x:int(x),date_time.split('-'))),4,58,00)
        delta = (d - datetime.now()).seconds
        log(person,"开启静默抢座模式")
        print ("程序将静待至{0}秒后运行".format(delta));
        time.sleep(delta)
    
    while person.login():
        log(person,person.err_msg)
        time.sleep(5)
    
    while person.islogin is False:
        log(person, person.err_msg)
        person.login()
        time.sleep(5)
    seat_name = "UNKNOWN"
    seat_lists = [(x['id'], x['name']) for x in person.get_room_seats_list(room_id, date_time)]
    if isinstance(seat_id,int):
        for i in seat_lists:
            if i[0] == seat_id:
                seat_name = i[1]
                break
    retry_count = 0
    booked = False
    show_count = 0
    log(person, "将要开启抢座任务，时间："+date_time+",开始时间:"+str(start_time/60)+",结束时间:"+str(end_time/60)+",座位号："+str(seat_name)+", ID:"+str(seat_id))
    while retry_count < 500:
        gc.collect()
        try:
            dates_list = person.get_book_date_filters()
        except Exception as e:
            log(person, e)
            time.sleep(5)
            continue

        if dates_list is False:
            if "密码" in person.err_msg:
                log(person, "密码鉴权失败，将重新登录")
                person.login()
                time.sleep(3)
                retry_count += 1;
                continue
            elif "维护" in person.err_msg:
                log(person, "系统正在维护，请稍后登录")
                time.sleep(30)
                continue
            elif "网络" in person.err_msg:
                log(person, "网络被封，正在休息。。。")
                time.sleep(900)
                continue
            else:
                log(person, person.err_msg)
                time.sleep(3)
                continue

        if date_time in dates_list:
            if seat_id == "Random":
                print('----------------------------------------------------------')
                log(person,"进行随机抢座位")
                print('----------------------------------------------------------')
                for i in seat_lists:
                    log(person,"开始随机抢【"+str(i[1])+"】,ID:"+str(i[0]))
                    if person.book_seat(i[0],date_time,start_time,end_time) is not False:
                        booked = True
                        break
                    else:
                        log(person, "抢【" + str(i[1]) + "】,ID:" + str(i[0])+"结果失败："+person.err_msg)
                    time.sleep(3)
            elif isinstance(seat_id,int):
                log(person, "开始抢座位ID:" + str(seat_id))
                if person.book_seat(seat_id, date_time, start_time, end_time) is not False:
                    booked = True
                    break
                else:
                    log(person, "抢座位ID【" + str(seat_id) + "】 结果失败：" + person.err_msg)
                if "失败" in person.err_msg:
                    seat_id = "Random"
                    continue
                elif "有效预约" in person.err_msg:
                    booked = True
                    break
            elif isinstance(seat_id,list):
                # 未实现
                pass
        else:
            if show_count % 200 == 0:
                log(person, "当前抢座暂未开放,正在等待抢位")
            show_count += 1
        time.sleep(3)
        if booked:
            break


if __name__ == '__main__':
	"""
        multi-thread for multi-user use.
        
        I have not check the maximum user this program could handle yet, But I recommend that you DO NOT run threads 
        more than 10  to prevent the risk of ip blocked of this script.
        学号，密码，房间（第几阅览室）【查询 get_book_date_filters】，座位ID，开始时间（分钟），结束时间（分钟），日期
    """
	if len(sys.argv) > 1 and sys.argv[1] == "seat":
		print("座位id查询工具>>>")
		user = input("请输入您的用户名: ")
		pwd  = input("请输入{0}的密码: ".format(user))
		person = SeatUtility({'username': user, 'password': pwd});
		if person.login():
			print("该用户登陆失败，请检查用户名与密码是否正确！")
			sys.exit(0)
		school = int(input("请输入校区，1为东校区，2为西校区:"));
		school = school if school in (1,2) else 2
		if(school is 1):
			print("您选择的是东校区")
		else:
			print("您选择的是西校区")
		# infos = get_free_room_list(self, schoolid=school)
		for i in person.get_free_room_list(schoolid=school):
			print(i['roomId'],"<=>",i['room'])
		roomId = int(input("请根据序号输入您要选择的房间："))
		seatname = int(input("请输入您的座号："))
		# print(person.get_room_seats_list(roomId));
		for i in person.get_room_seats_list(roomId):
			if i['name'] == "%03d" % seatname:
				print("------------------------------------")
				print("您的位置信息已找到!")
				print("请在users的dict里面添加下面的一行")
				print(r'"name1":("%s","%s",%d,%d,开始时间,结束时间   )' % (user,pwd,roomId,i['id']))
				print("注意逗号问题！")
				print("开始时间和结束时间都是按分钟计算比如早上7点是60*7 = 420")
				print("------------------------------------")
				sys.exit(0)
		sys.exit(0)
	else:	
	    users = {
	    	"name1":("220151214007","161624",23,8053,540,1320 )
	    }
	    fake_thread_pool = []
	    for k,v in users.items():
	    	print("deploying ",k,"....")
	    	tmpThread = threading.Thread(target=thread_seat_lock,args=v)
	    	tmpThread.start()
	    	time.sleep(1);
	    print("All Deployed ?");




