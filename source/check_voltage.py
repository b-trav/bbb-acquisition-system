#!/usr/bin/python3

import subprocess
import syslog
import time

raw_ave = 0.0
for n in range(1,11):
	raw_voltage_str = subprocess.check_output(['cat','/sys/bus/iio/devices/iio:device0/in_voltage0_raw']).decode("utf-8").strip()
	raw_voltage = float(raw_voltage_str)
	raw_ave = raw_ave + (raw_voltage - raw_ave)/n
	time.sleep(0.1)

r_1 = 9.925e3
r_2 = 910.0 
r_loss = 0.114 #This is the loss in voltage due to resistance before the voltage divider.
voltage = (raw_ave/2**12)*1.8*(r_1 + r_2)/r_2 + r_loss

#print("{:6.2f}V average raw ADC reading : {}/{:d}".format(voltage,raw_ave,2**12))
print("{:6.2f}".format(voltage))

if (voltage < 5.0):
	# We are obviously running on usb power, so do nothing
	pass
elif (voltage < 9.5):
	# We are running on battery, and it is getting flat, so shutdown
	syslog.syslog("Battery is getting flat ({:4.2f}V)- shutting down".format(voltage))
	subprocess.call("/usr/local/bin/bbbas_powerdown.py")

