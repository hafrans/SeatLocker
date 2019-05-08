
"""
 campus ID
"""



CONFIG_BUNDLE = {
    "UJN": {
        "BASE": "https://seat.ujn.edu.cn:8443",
        "NAME": "济南大学",
        "START": [7,0], #开始预约时间
        "ENTRY": [7,0], #图书馆开门时间
        "CAMPUS": {
            1: {
                'id':1,
                'name': "东校区",
                'IP': ""  # NCK
            },
            2: {
                'id':2,
                'name': "西校区",
                'IP': "10.167.149.242"  # NCK
            }
        }
    },
    "LCU":{
        "BASE":"http://lib-seat.lcu.edu.cn",
        "NAME":"聊城大学",
        "START": [5,0],
        "ENTRY": [7,0], #图书馆开门时间
        "CAMPUS":{
            1:{
                'id':1,
                'name':'西校区',
                'IP':""
            },
            2:{
                'id':2,
                'name':'东校区',
                'IP':""
            }

        }
        
    }


}

UNIVERSITY_OF_JINAN = "UJN"
LIAOCHENG_UNIVERSITY = "LCU"




def SCHOOL(schoolName):
    """
      获取学校配置
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]

def NAME(schoolName):
    """
      获取学校名称
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]["NAME"]

def BASE(schoolName):
    """
      获取学校服务器
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['BASE']

def CAMPUS(schoolName,campusId = 1):
    """
      获取校区配置
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['CAMPUS'][campusId]

def ALLCAMPUS(schoolName):
    """
      获取所有校区
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['CAMPUS']

def CAMPUS_NAME_ID_LIST(schoolName):
    """
      获取校区-ID对
    """
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return [{'name': y['name'] , 'id' : x} for x,y in CONFIG_BUNDLE[schoolName]['CAMPUS'].items()]

def CAMPUS_ID_LIST(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return  list(CONFIG_BUNDLE[schoolName]['CAMPUS'].keys())

def SCHOOL_NAME_KEY_LIST():
    """
    获取 学校 - KEY对
    """
    return [{'name':y['NAME'],'key':x} for x,y in CONFIG_BUNDLE.items()]

def SCHOOL_KEY_LIST():
    """
      获取所有学校的KEY
    """
    return  list(CONFIG_BUNDLE.keys())

def CAMPUS_CHECKIN_ENABLED(campus):
    """
      检查这个校区是否开启自动签到。
    """
    if campus['IP'] == "":
        return False
    else:
        return True

def SCHOOL_START_BOOK(schoolName):
    """
      获取学校开始预约的时间
    """
    return SCHOOL(schoolName)['START']

def SCHOOL_START_ENTRY(schoolName):
    """
      获取学校入场时间
    """
    return SCHOOL(schoolName)['ENTRY']


    
