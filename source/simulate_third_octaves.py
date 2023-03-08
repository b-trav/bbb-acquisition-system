#!/usr/bin/env python
import socket
import argparse
import numpy as np
import time
import datetime

def main(args):

    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP

    #Calculate the bands that we are using
    # f_c is a list of the centre frequency
    # The 19th centre frequency is defined to be 1000 Hz
    centre_frequency = 1000*np.power(2,(-18.)/3)                                 
    f_c = [int(round(centre_frequency))]
    upper_frequency = centre_frequency*np.power(2,1./6)
    while upper_frequency < args.sample_rate/2 :
        centre_frequency *= np.power(2,1./3)
        upper_frequency = centre_frequency*np.power(2,1./6)
        f_c.append(int(round(centre_frequency)))

    f_c.pop() #Get rid of the last entries

    min = -70
    max = -20
    start = min
    stop = max
    
    if args.fft_size == None:
        fft_size = args.sample_rate
    else:
        fft_size = args.fft_size    
    
    num_grabs = int(float(args.time) * float(args.sample_rate)/float(fft_size))
    
    for x in range(num_grabs):
        i = x+1
        start += 1
        if start == max:
            start = min
        stop += -1
        if stop == min:
            stop = max
        data = "[{},{},{},{},{},{},{}]".format(
            i,
            num_grabs,
            args.num_channels,
            args.sample_rate,
            fft_size,
            int(time.mktime(datetime.datetime.now().timetuple())),
            np.random.random_integers(0,1200000)
            )
        values = np.transpose(np.linspace(start,stop,len(f_c)))
        for x in range(args.num_channels):
            data += '[' + np.array_str(values+10*x,max_line_width=10000,precision=2) + ']'   
        if args.verbose:
            print("Attempting to send on {}:{}".format(args.ip,args.port))
            print "message:", data
        sock.sendto(data, (args.ip, args.port))
        time.sleep(float(fft_size)/float(args.sample_rate))
    
    sock.sendto('Finished', (args.ip, args.port))

if __name__ == '__main__':

    help_text = '''
    This script tests a UDP protocol.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument('-v', '--verbose', help="Show some additional info, useful for debugging.",action="store_true")
    parser.add_argument('-p', '--port', help="Port to communicate on",type=int,default=5005)
    parser.add_argument('-i', '--ip', help="IP address to communicate on",default="192.168.7.1")
    parser.add_argument('-n', '--num_channels', help="The number of channels",type=int,default=2)
    parser.add_argument('-s', '--sample_rate', help="The sample rate",type=int,default=65104)
    parser.add_argument('-N', '--fft_size', help="Length of fft",type=int)
    parser.add_argument('-t', '--time', help="Record length (in seconds)",type=int,default=10)
    args = parser.parse_args()  
    main(args)
