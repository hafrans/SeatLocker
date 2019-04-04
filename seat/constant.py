
"""
 campus ID
"""



CONFIG_BUNDLE = {
    "UJN": {
        "BASE": "http://seat.ujn.edu.cn",
        "NAME": "济南大学",
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
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]

def NAME(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]["NAME"]

def BASE(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['BASE']

def CAMPUS(schoolName,campusId = 1):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['CAMPUS'][campusId]

def ALLCAMPUS(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return CONFIG_BUNDLE[schoolName]['CAMPUS']

def CAMPUS_NAME_ID_LIST(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return [{'name': y['name'] , 'id' : x} for x,y in CONFIG_BUNDLE[schoolName]['CAMPUS'].items()]

def CAMPUS_ID_LIST(schoolName):
    if schoolName == None:
        raise ValueError("INPUT SCNAME")
    return  list(CONFIG_BUNDLE[schoolName]['CAMPUS'].keys())

def SCHOOL_NAME_KEY_LIST():
    return [{'name':y['NAME'],'key':x} for x,y in CONFIG_BUNDLE.items()]

def SCHOOL_KEY_LIST():
    return  list(CONFIG_BUNDLE.keys())

def CAMPUS_CHECKIN_ENABLED(campus):
    if campus['IP'] == "":
        return False
    else:
        return True
    
