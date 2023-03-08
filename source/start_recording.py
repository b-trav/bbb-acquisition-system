#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  start_recording.py
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
import os
import pwd
import grp
import datetime
import sys
import stat
import re
import xml.etree.ElementTree as etree
import shutil
import kill_services
from argparse import Namespace

BPS = "24"
V_MIN = "-5 V"
V_MAX = "5 V"
SDcard = "/mnt/externalSD"
curr_dir = os.getcwd()
source_dir = "/home/debian/bbb-acquisition-system/source"
web_dir = "/home/debian/bbb-acquisition-system/web"
config_file = SDcard + "/.current_config_xml"
default_config_file = web_dir + "/default_config.xml"
recordings_xml = SDcard + "/.recordings_xml"
default_recordings_file = web_dir + "/default_recording_settings.xml"
if not os.path.isdir("/var/lock/bbbas"):
    os.mkdir("/var/lock/bbbas")
    uid = pwd.getpwnam("debian").pw_uid
    gid = grp.getgrnam("debian").gr_gid
    os.chown('/var/lock/bbbas', uid, gid)
recording_lock_file = "/var/lock/bbbas/recording.lock"
mem_start_file = SDcard + "/.mem_start"
UDP_PORT = "5004"
ip_file = SDcard + "/.client_ip"
if os.path.isfile(ip_file):
    with open(ip_file) as f:
        UDP_IP = f.readline()
else:        
    UDP_IP = "192.168.7.1"
    
def disk_exists(path):
    try:
        return stat.S_ISBLK(os.stat(path).st_mode)
    except:
        return False

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

def main():
    
    # Figure out if the SD card is loaded
    try:
        binary_file_space = 512 * int(open('/sys/block/mmcblk0/mmcblk0p2/size'.format(**locals())).read())
        if not os.path.isfile(mem_start_file):
            with open(mem_start_file, "w") as f:
                f.write("0\n")
            mem_start = 0
        else:
            with open(mem_start_file, "r") as f:
                mem_start = int(f.readline().split()[0])
        free_space = binary_file_space - mem_start
    except Exception as e:
        print("There appears to be a problem with the SD card.")
        print("NB: SD card needs to be inserted before booting.")
        print("Exception: {}".format(e))
        sys.exit(1)

    if os.path.isfile(recording_lock_file):
        print("ERROR: Recording is already running")
        sys.exit(1)
    
    # Load a config file
    if not os.path.isfile(config_file):
        shutil.copyfile(default_config_file, config_file)
    config_tree = etree.parse(config_file)
    config = config_tree.getroot()    
    filename = config.find('filename').text
    if not filename:
        filename = 'bbbas'
    sample_rate = config.find('sample-rate').text
    num_channels = config.find('channels').text
    if 'shift' in config.find('channels').attrib :
        shift = "shift"
    else :
        shift = ""
    max_record_length = int(free_space / (int(sample_rate) * int(num_channels) * int(BPS) / 8))

    # Load the recordings file
    if not os.path.isfile(recordings_xml):
        shutil.copyfile(default_recordings_file, recordings_xml)
    disk_tree = etree.parse(recordings_xml)
    disk = disk_tree.getroot()        

    # Get the record length
    try:
        record_length = int(config.find('record_length').text)
    except:
        record_length = max_record_length

    #Turn a bunch of stuff off before recording
    kill_services.main(Namespace(start=False))

    # Get a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    binary_out_file = SDcard + '/' + filename + "_" + timestamp + ".bin"
        
    # Write timestamp and record_length to lock file
    with open(recording_lock_file, "w") as f:
         f.write("{} {}\n{}\n".format(timestamp,record_length,binary_out_file)) 

    print("INFO: Starting acquisition of {} at {}".format(filename,timestamp))

    # Write all the metadata to the recording file
    r = etree.SubElement(disk,'recording')
    x = etree.SubElement(r,'mem_start')
    x.text = "{}".format(mem_start)
    x = etree.SubElement(r,'mem_size')
    x = etree.SubElement(r,'filename')
    x.text = filename
    x = etree.SubElement(r,'record_length')
    x = etree.SubElement(r,'description')
    x.text = config.findall('description')[0].text
    x = etree.SubElement(r,'channels')
    x.text = num_channels
    for i in range(1,int(num_channels)+1):
        x = etree.SubElement(r,'channel_{}'.format(i))
        x.text = config.findall('channel_{}'.format(i))[0].text
    x = etree.SubElement(r,'bps')
    x.text = BPS
    x = etree.SubElement(r,'sign')
    x.text = 'signed'
    x = etree.SubElement(r,'endian')
    x.text = 'little'
    x = etree.SubElement(r,'sample-rate')
    x.text = sample_rate
    x = etree.SubElement(r,'min')
    x.text = V_MIN
    x = etree.SubElement(r,'max')
    x.text = V_MAX
    x = etree.SubElement(r,'recorded')
    x.text = timestamp

    #etree.SubElement(disk,x)
    indent(disk)
    disk_tree.write(recordings_xml, encoding="utf-8", xml_declaration=True)

    # Start the recording
    os.chdir(source_dir)
    subprocess.call("nice --18 ./acquire_data {} {} {} {} {} {}".format(
        record_length,
        sample_rate,
        num_channels,
        UDP_IP,
        UDP_PORT,
        shift
        ).split())
    print("Finished acquiring data")

    #Update the record length in the recording file
    with open(mem_start_file, "r") as f:
        mem_stop = int(f.readline().split()[0])
        mem_size = mem_stop - mem_start;
    r.find('mem_size').text = "{}".format(mem_size)
    r.find('record_length').text = "{}".format(int(mem_size/(int(sample_rate) * int(num_channels) * int(BPS) / 8) ))
    
    if os.path.isfile('/tmp/bbbas_drops'):
        with open('/tmp/bbbas_drops',"r") as f:
            drops = f.readline()[:-1]
            r.find('recorded').attrib['drops'] = drops
            print(drops)
        os.unlink('/tmp/bbbas_drops')
    disk_tree.write(recordings_xml, encoding="utf-8", xml_declaration=True)
    
    #Turn a bunch of stuff on after recording
    kill_services.main(Namespace(start=True))

    if os.path.isfile(recording_lock_file):
        os.remove(recording_lock_file);
        
    os.chdir(curr_dir)
        
    return 0

if __name__ == '__main__':
    main()

