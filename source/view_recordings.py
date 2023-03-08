#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  view_recordings.py
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
import xml.etree.ElementTree as etree
import datetime
import re
import convert_flac

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


sd_dir = os.path.dirname(os.path.realpath(__file__))
recordings_xml = sd_dir + "/.recordings_xml"

if not os.path.isfile(recordings_xml):
    print("There are no recordings on this SD card.")
    sys.exit(1)

disk_tree = etree.parse(recordings_xml)
disk = disk_tree.getroot()		

num_recordings = len(disk.findall('recording'))
if not num_recordings:
    print("There are no recordings on this SD card.")
    sys.exit(1)
    
print('There are {} recordings on this SD card'.format(num_recordings))

with open("/proc/mounts",'r') as file:
    for line in file:
        if sd_dir in line:
            raw_disk = line.split(" ")[0]
            raw_disk = raw_disk[:-1] + '2'


#TODO: Remove this working dir
working_dir = '/home/btrav/Documents/bbb-acquisition-system/data'
#working_dir = input("Please enter a working directory (with plenty of space) :")
if not os.path.isdir(working_dir):
    print("This directory does not exist. Please choose/create a valid directory and re-run this script.")
    sys.exit(1)

cmd = 'X'

while (cmd != 'Q'):
    
    disk_tree = etree.parse(recordings_xml)
    disk = disk_tree.getroot()

    print("Recordings :")
    table_columns = '{:3} | {:15}| {:20}| {:9} | {:8}| {:3}| {:8}| {:30}|'
    print(table_columns.format("No.","Title","Recorded","Size (MB)", "Length", "Ch", "Rate", "Description"))
    for i, r in enumerate(disk.findall('recording')):
        print(table_columns.format((i + 1),
            r.find('filename').text,
            datetime.datetime.strptime(r.find('recorded').text,"%Y%m%d%H%M%S").strftime("%H:%M:%S %d/%m/%Y"),
            int(int(r.find('mem_size').text)/1024/1024),
            r.find('record_length').text,
            r.find('channels').text,
            r.find('sample-rate').text,
            r.find('description').text
            ))

    cmd = input("What would you like to do? (A)nalyze, (D)elete, (E)xport binary, export (F)lac, (Q)uit : ")
    if not cmd:
        cmd = 'X'
        continue
    else:
        cmd = cmd[0].upper()
    
    if (cmd == 'Q') :
        break;
    
    if (cmd == 'A'):
        full_cmd = 'analyze'
    elif (cmd == 'D'):
        full_cmd = 'delete'
    elif (cmd == 'E'):
        full_cmd = 'export to binary'
    elif (cmd == 'F'):
        full_cmd = 'export to flac'
    else:
        continue
        
    r_list_str = input("Which recordings would you like to " + full_cmd + "? (A)ll or a list of numbers :")
    if not r_list_str:
        cmd = 'X'
        continue
    elif (r_list_str[0].upper() == 'A') :
        selected_recordings = disk.findall('recording')
    else:
        r_list = [int(s) for s in re.split(';|,| ',r_list_str) if s.isdigit()]
        r_list = sorted(list(set(r_list)))
        selected_recordings = [disk.findall('recording')[i-1] for i in r_list]
            
    if (cmd == 'A'):
        full_cmd = 'analyze'
    elif (cmd == 'D'):
        for x in reversed(selected_recordings):
            disk.remove(x)
        indent(disk)
        disk_tree.write(recordings_xml, encoding="utf-8", xml_declaration=True)
        print("Deleted recording(s).")
    elif (cmd == 'E') or (cmd == 'F'):
        for x in reversed(selected_recordings):
            filename = '{}/{}_{}'.format(working_dir,x.find('filename').text,x.find('recorded').text)
            print('Exporting to {}.xml'.format(filename))
            etree.ElementTree(x).write('{}.xml'.format(filename), encoding="utf-8", xml_declaration=True)
            mem_start = int(x.find('mem_start').text)
            mem_size = int(x.find('mem_size').text)
            buffer_size = int( int(x.find('channels').text)*int(x.find('bps').text)*int(x.find('sample-rate').text)/8 )
            print("Copying {} bytes from {} starting at {} to {}.bin in chunks of {}".format(mem_size,raw_disk,mem_start,filename,buffer_size))
            with open(raw_disk,'rb') as raw_in_f:
                raw_in_f.seek(mem_start)
                with open(filename + ".bin",'wb') as bin_out:
                    while raw_in_f.tell() < (mem_start + mem_size):
                        buf = raw_in_f.read(buffer_size)
                        bin_out.write(buf)
            if (cmd == 'F'):
                convert_flac.main(filename)
