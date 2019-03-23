from seat.__future__ import *

if __name__ == "__main__":
    try:
        p = SeatClient.NewClient("20170000000","0000000")
        if p.checkIn()['code'] == '0':
            print("签到成功")
    except UserCredentialError as e:
        print(e)
    except SystemMaintenanceError as e:
        print(">>>系统正在维护")