#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  start_analysing.py
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

import numpy as np
import os
import subprocess
import datetime
import time
import struct
import sys
import xml.etree.ElementTree as etree
import socket
import argparse
import shutil
import kill_services
from argparse import Namespace

def indent(elem, level=0):
	i = "\n" + level*"  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level+1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i

def main(args):

    BPS = "24"
    V_MIN = "-5 V"
    V_MAX = "5 V"
    SDcard = "/mnt/externalSD"
    curr_dir = os.getcwd()
    source_dir = "/home/debian/bbb-acquisition-system/source"
    web_dir = "/home/debian/bbb-acquisition-system/web"
    octaves_xml = SDcard + "/.octaves_xml"
    default_recordings_file = web_dir + "/default_recording_settings.xml"
    config_file = SDcard + "/.current_config_xml"
    default_config_file = web_dir + "/default_config.xml"
    recording_lock_file = "/var/lock/bbbas/recording.lock"
    if not os.path.isdir("/var/lock/bbbas"):
        os.mkdir("/var/lock/bbbas")
        uid = pwd.getpwnam("debian").pw_uid
        gid = grp.getgrnam("debian").gr_gid
        os.chown('/var/lock/bbbas', uid, gid)
    tmp_link = "/tmp/bbbas.octaves"
    RAM_file = "/dev/shm/bbbas"
    UDP_PORT = args.port
    ip_file = SDcard + "/.client_ip"
    if os.path.isfile(ip_file):
        with open(ip_file) as f:
            UDP_IP = f.readline()
    else:        
        UDP_IP = args.ip


    if os.path.isfile(recording_lock_file):
        print("ERROR: Recording is already running")
        sys.exit(1)

    # Write timestamp and record_length to lock file
    with open(recording_lock_file, "w") as f:
         f.write("Getting octaves\n") 

    # Load a config file
    if not os.path.isfile(config_file):
        shutil.copyfile(default_config_file, config_file)
    config_tree = etree.parse(config_file)
    config = config_tree.getroot()    
    filename = config.find('filename').text
    if not filename:
        filename = 'bbbas'
    sample_rate = int(config.find('sample-rate').text)
    num_channels = int(config.find('channels').text)
    record_length = int(config.find('record_length').text)
    if 'shift' in config.find('channels').attrib :
        shift = "shift"
    else :
        shift = ""
    fft_size = config.find('fft_size').text
    if fft_size == None:
        fft_size = sample_rate
    else:
        fft_size = int(fft_size)    

    # Load the recordings file
    if not os.path.isfile(octaves_xml):
        shutil.copyfile(default_recordings_file, octaves_xml)
    disk_tree = etree.parse(octaves_xml)
    disk = disk_tree.getroot()        

    # Get the record length
    try:
        record_length = int(config.find('record_length').text)
    except:
        record_length = 3600
        
    num_grabs = int(float(record_length)/float(fft_size)*float(sample_rate))
    fft_max_time = int(1000000.*float(fft_size)/float(sample_rate))

    print("num_grabs : {}, sample_rate : {}, fft_size : {}, num_channels : {}, {}".format(num_grabs,sample_rate,fft_size,num_channels,shift))

    #Turn a bunch of stuff off before recording
    kill_services.main(Namespace(start=False))

    N = fft_size
    delta_f = float(sample_rate)/float(fft_size)
    #Calculate the bands that we are using
    # f_c is a list of the centre frequencies of each band
    # f_w is a list of the band-width of each band
    # f_e is a list of the band limits (it is one element longer than f_c)
    # The 19th centre frequency is defined to be 1000 Hz
    centre_frequency = 1000*np.power(2,(-18.)/3)                                 
    f_c = [int(round(centre_frequency))]
    upper_limit = centre_frequency*np.power(2,1./6)
    f_e = [int(centre_frequency/np.power(2,1./6)/delta_f), int(upper_limit/delta_f)]
    f_w = [upper_limit - centre_frequency/np.power(2,1./6)]
    while upper_limit < sample_rate/2 :
        centre_frequency *= np.power(2,1./3)
        upper_limit = centre_frequency*np.power(2,1./6)
        f_c.append(int(round(centre_frequency)))
        f_w.append(upper_limit - f_w[-1])
        f_e.append(int(upper_limit/delta_f))

    #Get rid of the last entries
    f_c.pop()
    f_e.pop()
    f_w.pop()
    octaves = np.zeros([len(f_c),1])
    
   # Get a timestamp
    file_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Write all the metadata to the recording file
    r = etree.SubElement(disk,'recording')
    x = etree.SubElement(r,'centre_frequencies')
    x.text = "{}".format(str(f_c))
    x = etree.SubElement(r,'filename')
    x.text = filename
    x = etree.SubElement(r,'record_length')
    x = etree.SubElement(r,'description')
    x.text = config.findall('description')[0].text
    x = etree.SubElement(r,'channels')
    x.text = "{}".format(num_channels)
    for i in range(1,int(num_channels)+1):
        x = etree.SubElement(r,'channel_{}'.format(i))
        x.text = config.findall('channel_{}'.format(i))[0].text
    x = etree.SubElement(r,'sample-rate')
    x.text = "{}".format(sample_rate)
    x = etree.SubElement(r,'fft_size')
    x.text = "{}".format(fft_size)
    x = etree.SubElement(r,'min')
    x.text = V_MIN
    x = etree.SubElement(r,'max')
    x.text = V_MAX
    x = etree.SubElement(r,'recorded')
    x.text = file_timestamp

    #etree.SubElement(disk,x)
    indent(disk)
    disk_tree.write(octaves_xml, encoding="utf-8", xml_declaration=True)
    
    octaves_out_file = SDcard + '/' + filename + "_" + file_timestamp + ".octaves"

    subprocess.call("nice --18 ./data_to_ram {} {} {} {} {} {} {}".format(
        record_length, #argv 1
        sample_rate, #argv 2
        fft_size, #argv 3
        num_channels, #argv 4
        UDP_IP, #argv 5
        UDP_PORT, #argv 6
        shift #argv 7
        ).split(),cwd=source_dir)
    print("Finished measuring 1/3 octaves")

    shutil.copyfile(RAM_file, octaves_out_file)
        
    i = sum(1 for line in open(octaves_out_file))
    #Update the record length in the recording file
    r.find('record_length').text = "{}".format(int(float(i)*float(fft_size)/float(sample_rate)))
    #Record if any packets were dropped
    if os.path.isfile('/tmp/bbbas_drops'):
        with open('/tmp/bbbas_drops',"r") as f:
            drops = f.readline()[:-1]
            r.find('recorded').attrib['drops'] = drops
            print(drops)
        os.unlink('/tmp/bbbas_drops')
    disk_tree.write(octaves_xml, encoding="utf-8", xml_declaration=True)

    #Turn a bunch of stuff on after recording
    kill_services.main(Namespace(start=True))

    #Remove the file which puts recording into octave mode
    if os.path.isfile('/tmp/octaves'):
        os.unlink('/tmp/octaves')

    if os.path.isfile(recording_lock_file):
        os.remove(recording_lock_file);
        

if __name__ == '__main__':

    help_text = '''
    This script records third-octave information, and send the data over a UDP channel.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument('-v', '--verbose', help="Show some additional info, useful for debugging.",action="store_true")
    parser.add_argument('-p', '--port', help="Port to communicate on",type=int,default=5005)
    parser.add_argument('-i', '--ip', help="IP address to communicate on",default="192.168.7.1")
    args = parser.parse_args()  
    main(args)
