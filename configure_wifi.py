#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  configure_wifi.sh
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

import os
import sys
import re

wpa_file = "/etc/wpa_supplicant/wpa_supplicant.conf"

new_network = '''
network={{
	ssid="{}"
	proto=WPA2
	key_mgmt=WPA-PSK
	pairwise=CCMP TKIP
	group=CCMP TKIP
	psk="{}"
	priority={}
}}

''' 
	
file_start = '''
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

''' 				

if not os.path.isfile(wpa_file):
	with open(wpa_file, "w") as f:
		 f.write(file_start) 

with open(wpa_file, "r") as f:
	 wpa_text = f.read() # read everything in the file

cmd = 'X'

print("This configure script assumes that you are setting up WPA2 wifi networks.")
print("If this is not the case, then you need to configure " + wpa_file + " manually")

while (cmd != 'Q'):

	if not 'network' in wpa_text:
		print("There are currently no wifi networks configure.")
	else:
		print("Current networks:")
		print('{:4} | {:20}| {:20}| {:9}|'.format("No.","Network","Password","Priority"))
		networks = re.findall(new_network.format("(.+?)","(.+?)","(.+?)"), wpa_text)
		for idx, n in enumerate(networks) :
			print('{:4} | {:20}| {:20}| {:9}|'.format((idx + 1),n[0],n[1],n[2]))

	cmd = input("What would you like to do? (A)dd a network, (D)elete a network, (S)ave and exit, (Q)uit : ")[0].upper()

	if (cmd == 'A'):
		ssid = input("SSID : ")
		passwd  = input("Password : ")
		priority = input("Priority 1-10 (lower to higher) :")
		wpa_text += new_network.format(ssid,passwd,priority)
		print(wpa_text)
	elif (cmd == 'D'):
		net_int = int(input("Which network would you like to delete? "))
		n = networks[net_int - 1]
		wpa_text = re.sub(new_network.format(n[0],n[1],n[2]),'',wpa_text)
	elif (cmd == 'S'):
		with open(wpa_file, "w") as f:
			 f.write(wpa_text)
		cmd = 'Q'
