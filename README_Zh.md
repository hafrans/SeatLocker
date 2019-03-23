# UJN图书馆座位助手+API

中文版 | [English](./README.md)

> 我们重构了所有的代码，实现了一个全新的插件库。
> 目前的版本正在开发中，很快就有新版本诞生。目前的版本将会在下次的版本迭代中正式废弃，之后不会
> 收到任何的修复与支持，此插件在之后的时间依旧还可以使用

### 预览版本尝鲜
clone future 分支后查看example.py
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

## 插件功能
  * 实现自动快速预约
  * 可以在命令行下使用 'python ./seatLocker.py seat' 实现自助选座
  * 脚本提供了SeatUtility，可以实现二次开发

## 插件特色
  * 稳定性极高，时钟任务挂机200天（1 Core 512M RAM ）不出问题
  * 当前位置被别人抢后，自动开启随机抢座模式，防止自己的座位落空
  * 支持二次开发

## 环境要求
  * Python 3.5 +

## 使用方法
  1. clone 本仓库的所有代码
  2. 在打开当前目录的命令窗口，输入 'python ./seatLocker.py seat' (windows下为‘\’)，可以输入命令自助选座，讲控制台中输出的配置信息粘贴到脚本的规定区域中，可以参照脚本中的注释操作。
  3. 在打开当前目录的命令窗口，输入 'python ./seatLocker.py ' (windows下为‘\’),就可以自动进行预约操作了
  > 你可以使用时钟任务来达到每日抢座


## 开发日志

#### Automatic Reserving Script
 * 1.0.0 the script is finished.


#### SeatUtilty
 * 1.0.0 SeatUtilty is finished.


 **注意**
 *_这个脚本仅供学习与研究使用，严禁将其用于破坏图书馆管理规定的违规情形，或用其做为非法盈利手段，所造成的一切后果由个人承担_*


 @tensorflower