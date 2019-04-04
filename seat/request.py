


"""
    A Wrapped Request For Seat Reservation

"""

import urllib
import urllib.request
import urllib.parse
import logging
import json
from .exception import NetWorkException
from .constant import *

class WrappedRequest(object):
    """
        WrappedRequest Class
        This class provides a delegation for urllib.
    """

    ROUTER = {
        "AUTH": "/rest/auth",
        "RESV": "/rest/v2/user/reservations",
        "FFTR": "/rest/v2/free/filters",
        "RMST": "/rest/v2/room/stats2/{campus}",
        "LOBD": "/rest/v2/room/layoutByDate/{roomId}/{date}",
        "STFS": "/rest/v2/startTimesForSeat/{seatId}/{date}",
        "ETFS": "/rest/v2/endTimesForSeat/{seatId}/{date}/{startTime}",
        "BOOK": "/rest/v2/freeBook",
        "CKIN": "/rest/v2/checkIn",
        "STOP": "/rest/v2/stop",
        "HSTY": "/rest/v2/history/1/20",
        "CACE": "/rest/v2/cancel/{id}"
    }

    __default_headers_template = {
        "Host": "",
        "Connection": "Keep-Alive",
        "User-Agent": "",
        "token": "",
        "Accept-Encoding":"gzip, deflate",
    }

    def __init__(self, campus,school):
        """
        initialize instance with correct headers
        campus = 必须包含（1）校区名称 （2）IP地址
        """

        self.headers = WrappedRequest.__default_headers_template.copy()
        #修改BASE
        self.headers['Host'] = urllib.parse.urlparse(BASE(school)).netloc
        self.school = school
        self.opener = urllib.request.urlopen
        self.__region = campus
        pass

    @staticmethod
    def makeQuickCheckIn(token):
        pass

    @property
    def region(self):
       return self.__region

    @region.setter
    def region(self, campus):
        """
          set the region of campus west or east or other
        """
        #多校区折衷方案
        self.__region = campus

    @property
    def token(self):
        """
          get token which could identify one's status
        """
        return self.headers['token']

    @token.setter
    def token(self, token):
        """
        set token
        :param token the token you will set.
        """
        if len(token) < 5:
            return False
        else:
            self.headers['token'] = token
            return True

    def urlencode(self, payload={}, charset="UTF-8"):
        return urllib.parse.urlencode(payload, encoding=charset)

    def request(self, route=None, url=None, payload=None, post=None, append_mode=False,forwardIP = False):
        """
            Send Request To Server.
        """
        url_route_flag = False
        _url = ""
        _data = ""
        _post = None
        _head = self.headers
        request = None

        if route == None and url == None:
            raise AttributeError("either route or url is not specified")
        if route != None:
            _url = WrappedRequest.ROUTER.get(route, None)
            if _url == None:
                raise AttributeError("Route name Not Found!")
            _url = BASE(self.school) + _url
        elif url != None:
            _url = url
            url_route_flag = True

        if payload != None:
            _data = self.urlencode(payload)

        if post != None:
            _post = str.encode(self.urlencode(post), encoding='UTF-8')

        if forwardIP == True:
            logging.debug("USING FORWARD HEAD")
            _head = self.headers.copy()
            # TODO 要进行多校区处理
            _head['X-Forwarded-For'] = self.__region['IP']

        if url_route_flag or append_mode:  # use url
            request = urllib.request.Request(
                _url + "?" + _data, data=_post, headers=_head)
            logging.debug("send request to %s", _url)
        elif payload != None:
            request = urllib.request.Request(_url.format(
                **payload), data=_post, headers=_head)
            logging.debug("send request to %s", _url.format(**payload))
        else:
            request = urllib.request.Request(
                _url, data=_post, headers=_head)
            logging.debug("send request to %s with %s", _url, post)

        resp = self.opener(request)

        if resp.status == 200 and resp.getheader("Content-Length") != "0":
            return json.load(resp)
        else:
            raise NetWorkException("Network Error ({0},{1},{2})".format(
                resp.status, resp.getheader("Content-Length"), resp.read()))

