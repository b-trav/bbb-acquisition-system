#!/usr/bin/env python
import subprocess
import argparse
import xml.etree.ElementTree as etree
import os
import struct
import time

def get_tag(tag_name,filename):
    
    basename, file_type = os.path.splitext(filename)
    
    if (file_type == ".flac") :
        if (tag_name == "sample-rate") :
            tag_string = subprocess.check_output(["metaflac", "--show-sample-rate",filename])
        elif (tag_name == "bps") :
            tag_string = subprocess.check_output(["metaflac", "--show-bps",filename])
        elif (tag_name == "num_channels") :
            tag_string = subprocess.check_output(["metaflac", "--show-channels",filename])
        elif (tag_name == "num_samples") :
            tag_string = subprocess.check_output(["metaflac", "--show-total-samples",filename])
        else :
            tag_string = subprocess.check_output(["metaflac", ("--show-tag=" + tag_name) ,filename]).decode("utf-8")
            if tag_string :
                tag_string = tag_string.split("=")[1]
    elif (file_type == ".bin") :
        tree = etree.parse(basename + ".xml")
        config = tree.getroot()
        if (tag_name == "num_channels") :
            tag_string = config.findall("channels")[0].text
        elif (tag_name == "num_samples") :
            fs = int(config.findall("sample-rate")[0].text)
            record_length = int(float(config.findall("record_length")[0].text))
            tag_string = "{}".format( fs * record_length)
        else :
            tag_string = config.findall(tag_name)[0].text
    
    else :
        config, raw_disk, cache_dir = recording_info(filename)
        if (tag_name == "num_channels") :
            tag_string = config.findall("channels")[0].text
        elif (tag_name == "num_samples") :
            fs = int(config.findall("sample-rate")[0].text)
            record_length = int(float(config.findall("record_length")[0].text))
            tag_string = "{}".format( fs * record_length)
        else :
            tag_string = config.find(tag_name).text
                
    return tag_string


def main(args):
    
    sample_rate = int(get_tag("sample-rate" ,args.input))
    precision = int(get_tag("bps" ,args.input))
    num_channels = int(get_tag("num_channels" ,args.input))
    record_length = int(get_tag("record_length" ,args.input))

    with open("/dev/shm/bbbas","wb") as shared_memory :
        with open("/var/lock/bbbas.lock","wb") as lock_file:
            with open(args.input,'r') as binary_file:
                for i in range(record_length):
                    if (i % 2 == 0):
                        shared_memory.seek(0)
                    shared_memory.write(binary_file.read((precision/8)*num_channels*sample_rate))
                    lock_file.write(struct.pack("i",i+1))
                    lock_file.seek(0)
                    time.sleep(1)
                    
    os.remove("/var/lock/bbbas.lock")
                    

if __name__ == '__main__':
    
    help_text = '''
    This script simulates the data_to_ram program on the bbbas.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument("-s", '--sample-rate', help="The sample-rate of the data.",default="130208")
    parser.add_argument("-c", '--channels', help="The number of channels collected.",default="1")
    parser.add_argument("-n", '--length', help="The number of seconds of data to collect.",default="10")
    parser.add_argument("-i", '--input', help="A binary file containing raw data from the bbbas.")
    args = parser.parse_args()
    main(args)