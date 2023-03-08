#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  convert_flac.py
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

import xml.etree.ElementTree as etree
import subprocess
import sys
import os
import math

def execute(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline().decode(sys.stdout.encoding)
        if nextline == '' and process.poll() is not None:
            break        
        if nextline:
            print(nextline.strip())
            sys.stdout.flush()
        
def main(filename):
    
    filename = os.path.splitext(filename)[0]
    binary_out_file = filename + ".bin"
    info_file = filename + ".xml"
    
    if not os.path.isfile(info_file):
        print("ERROR: I need a metadata xml file, to convert this binary.")
        sys.exit(1)

    tree = etree.parse(info_file)
    config = tree.getroot()    
    
    # Check that the record_length is valid
    bps = int(config.find('bps').text)    
    sample_rate = int(config.find('sample-rate').text)
    num_channels = int(config.find('channels').text)
    file_size = os.path.getsize(binary_out_file)
    record_length = int(config.find('record_length').text)
    check_size = int(record_length * sample_rate * num_channels * (bps / 8))
    print("bps = {}, sample-rate = {}, channels = {}, file_size = {}, record_length = {}".format(bps,sample_rate,num_channels,file_size,record_length))
    if (check_size != file_size):
        print("ERROR: Something is wrong here!")
        sys.exit(1)
        
    # Convert the binary file into a flac file
    flac_filename = filename + ".flac"
    num_channels = int(config.find('channels').text)
    description = config.find('description').text
    recorded = config.find('recorded').text
    channel_str = ""
    for n in range(1,num_channels + 1):
        channel_str += '-T channel_{}="{}" '.format(n,config.find('channel_{}'.format(n)).text)
    min_v = config.find('min').text
    max_v = config.find('max').text
    flac_cmd = 'flac -f -T recorded="{}" -T min="{}" -T max="{}" -T description="{}" {} --channels={} --bps={} --sign=signed --endian=little --lax --sample-rate={} -o {} {}';
    flac_cmd = flac_cmd.format(recorded,min_v,max_v,description,channel_str,num_channels,bps,sample_rate,flac_filename,binary_out_file)
    execute(flac_cmd)
    
    # Delete the binary file and info file
    #os.remove(binary_out_file)
    #if os.path.isfile(info_file):
    #    os.remove(info_file)
        
    return 0

if __name__ == '__main__':
    main(sys.argv[1])

