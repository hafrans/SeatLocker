
""" 

   utils 
"""
import urllib
import re


def getPublicIP():
    result = urllib.request.urlopen("http://txt.go.sohu.com/ip/soip").read()
    return re.findall(r'\d+.\d+.\d+.\d+',result)[0]