# Automatic Library Booking System for University of Jinan V1.0
---  

[🇨🇳 中文版](./README_Zh.md) | English | [Doc](./seat/docs/build/index.html)

> We Have Refactored all script of SeatUtility. We Will Release SeatClient very soon. After new release , the SeatUtility and it's automatic reserving script
> will be deprecated and no longer receive any support.

### Try new features of seatclient in alpha
just clone future branch and follow example in example.py
``` python
from seat.__future__ import *

if __name__ == "__main__":
    try:
        p = SeatClient.NewClient("20170000000","0000000")
    except UserCredentialError as e:
        print("pwd not matched.")
    except SystemMaintenanceError as e:
        print(">>>系统正在维护")
```


## Functions
  * Automatic reserve seats
  * Finding seat your like by command 'python seatLocker.py seat' and generate a configuration variable for your seat.
  * You can develop your own script with the utility provided by seatLocker. You can follow the notes in seat/utility.py to get more details.

## Featues
  * Very stable. it has been runing on a vps (1C512M) for 200 days and not crash.
  * if your seat was reserved by others, it will start random reserving mode.
  * You can use seatutility to build your own script.

## Dependencies
  * Python 3.5+

## How to use 
  1. Download all resources from the repository.
  2. Type "python seatLocker.py seat" to choose one seat your like.
  3. Follow notes in seatLocker.py and modify the configuration variables to make it work.
  4. Just run "python seatLocker.py"
  > You can use crontab to make the script cycle execution.

## FAQ
   1. Another script which functions like this but reserving speed is faster. I want to make it to reserve seat more quickly, what should I do?
   > This script uses a time.sleep to control reserving speed. **on line 137 in seatLocker.py**, You will find a time.sleep(3). It means after doing instructions above, it will sleep 3 seconds. Just change it. like 'time.sleep(1)' it allows float number like 0.5, but I do not recommend you to do that because if the script does poll very fast the server will deny script's access for safety.  

## Logs

#### Automatic Reserving Script
 * 1.0.0 the script is finished.


#### SeatUtilty
 * 1.0.0 SeatUtilty is finished.






**Attentions**:
*_This program is built for research and study, DO NOT use it for other propers of violation of library's regulations._*



@tensorflower
  
