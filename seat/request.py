


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

    BASE_URL = "http://seat.ujn.edu.cn"


    EAST_CAMPUS = "10.167.149.241"  # WHO CAN PROVIDE ME A IP OF EC?
    WEST_CAMPUS = "10.167.149.242"


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
        "Host": urllib.parse.urlparse(BASE_URL).netloc,
        "Connection": "Keep-Alive",
        "User-Agent": "",
        "token": ""
    }

    def __init__(self, campus=WEST_CAMPUS):
        """
        initialize instance with correct headers
        """

        self.headers = WrappedRequest.__default_headers_template.copy()
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
    def region(self, campus=WEST_CAMPUS):
        """
          set the region of campus west or east or other
        """
        # if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", campus):
        #     self.headers['X-Forwarded-For'] = campus
        # else:
        #     logging.warning("set region failed %s", str(campus))
        if campus == WEST_CAMPUS or campus == EAST_CAMPUS:
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
            _url = WrappedRequest.BASE_URL + _url
        elif url != None:
            _url = url
            url_route_flag = True

        if payload != None:
            _data = self.urlencode(payload)

        if post != None:
            _post = str.encode(self.urlencode(post), encoding='UTF-8')

        if forwardIP == True:
            _head = self.headers.copy()
            _head['X-Forwarded-For'] = WrappedRequest.WEST_CAMPUS if self.__region == WEST_CAMPUS else WrappedRequest.EAST_CAMPUS

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

