#!/bin/bash


#
# SeatLocker
#

source /etc/profile
source /root/.bashrc

DATE=`date -d "+1day" +'%y-%m-%d'`

#source activate base

python -u /opt/seatLock.py | tee "/opt/tee-$DATE.log"



