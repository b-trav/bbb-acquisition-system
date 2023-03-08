#!/usr/bin/env python
import socket
import argparse

def main(args):

    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP

    if not args.receive:
        print("Attempting to send on {}:{}".format(args.ip,args.port))
        print "message:", args.message
        sock.sendto(args.message, (args.ip, args.port))	
        return 0


    sock.settimeout(args.timeout)
    print("Attempting to listen on {}:{} for {} seconds".format(args.ip,args.port,args.timeout))
    try:
        sock.bind((args.ip, args.port))
    except Exception as E:
        print("Failed : {}".format(E))
        return 0
    while True:
        try:
            data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
            print "received message:", data
        except Exception as e:
            pass
            #print "Timed out"
    return 0


if __name__ == '__main__':

    help_text = '''
    This script tests a UDP protocol.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument('-v', '--verbose', help="Show some additional info, useful for debugging.",action="store_true")
    parser.add_argument('-r', '--receive', help="Receive a UDP message",action="store_true")
    parser.add_argument('-s', '--send', help="Send a UDP message",action="store_true",default=True)
    parser.add_argument('-m', '--message', help="Send a UDP message",default="Hello World")
    parser.add_argument('-p', '--port', help="Port to communicate on",type=int,default=5005)
    parser.add_argument('-i', '--ip', help="IP address to communicate on",default="192.168.7.1")
    parser.add_argument('-t', '--timeout', help="listen time",type=float,default=1.)
    args = parser.parse_args()  
    main(args)
