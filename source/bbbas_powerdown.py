#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  bbbas_powerdown.py
#  
#  Copyright 2016 Ben Travaglione <ben@travaglione.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import subprocess
import sys
import os
import time

PIN = "31" # Corresponds to p9.13 (UART4_TXD) gpio0[31] corresponds to gpio31
recording_lock_file = "/var/lock/bbbas/recording.lock"

def main():
	
	if ( os.path.isfile(recording_lock_file) ):
		with open("/sys/class/gpio/gpio{}/value".format(PIN), "w") as pin_file:
			pin_file.write("1")
		time.sleep(1)
		with open("/sys/class/gpio/gpio{}/value".format(PIN), "w") as pin_file:
			pin_file.write("0")
		time.sleep(3)
	subprocess.call("poweroff")
	return 0

if __name__ == '__main__':
	main()

