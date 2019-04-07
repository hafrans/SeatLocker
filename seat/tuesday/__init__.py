# Tuesday strategy library.
import logging

logging.basicConfig(level=logging.DEBUG,
                    format="[%(levelname)s] %(asctime)s - %(message)s")

from .ujn import *

__all__ = ['TUESDAY_STRATEGY']
#register

TUES_STRA_MAP = {
    "UJN":ujn
}

def TUESDAY_STRATEGY(schoolName = "UJN"):
    return TUES_STRA_MAP.get(schoolName,defaultHandler)

def defaultHandler(layoutDate,startTime,endTime,tuesday = False):
    logging.info("Using Default Tuesday Strategy.")
    return startTime,endTime