#!/bin/bash

i=0
until hwclock -r -f /dev/rtc1; do
	(( i+= 1))
	if [ $i -eq 5 ]; then
		break
	fi
	echo "Waiting for real-time clock ..." >> /home/debian/test_log.txt
	echo "Waiting ..."
	sleep 5
done
