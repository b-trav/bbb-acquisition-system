#!/usr/bin/env python
import subprocess
import argparse


def main(args):
    #Check out dbus, rsyslog
    #Figure out how to stop systemd nicely
    service_list = ["apache2","cron","udhcpd","dbus"]
    job_list = ["dhclient","wpa_supplicant"]

    if args.start:
        print("Turning on all unnecessary services")
        for service in service_list:
            subprocess.call(["sudo","service",service,"start"])
        for service in job_list:
            print("    resuming {}".format(service))
            subprocess.call(["sudo","pkill","-SIGCONT",service])
    else:
        print("Turning off all unnecessary services")
        for service in service_list:
            subprocess.call(["sudo","service",service,"stop"])
        for service in job_list:
            print("    pausing {}".format(service))
            subprocess.call(["sudo","pkill","-SIGSTOP",service])
 
if __name__ == '__main__':
    
    help_text = '''
    This script kills a number of services, so that recording can continue
    uninterrupted.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument("-k", '--kill', help="Kill the services", action='store_true', default=True)
    parser.add_argument("-s", '--start', help="Start the services", action='store_true', default=False)
    args = parser.parse_args()
    main(args)
