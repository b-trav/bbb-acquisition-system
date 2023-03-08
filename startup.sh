#!/bin/bash
#
# startup.sh
#

ITWOC=/sys/class/i2c-adapter/i2c-2 #K4
CAPE_SLOTS=/sys/devices/platform/bone_capemgr/slots #K4

ITWOC=/sys/class/i2c-adapter/i2c-1 #K3
CAPE_SLOTS=/sys/devices/bone_capemgr.9/slots #K3

if [ ! -d $ITWOC/*68/ ]; then
	echo "bbb-as startup.sh : Waiting 15 seconds for the real-time clock to be ready ..."
	sleep 15
	echo "bbb-as startup.sh : Loading the clock"
	echo ds1307 0x68 > $ITWOC/new_device
	hwclock -s -f /dev/rtc1
	hwclock -w
fi

# Increasing the size of the PRU shared memory
# Setting to the max size of 8Mb 
# We actually only use a maximum of approx 6.2Mb :
# 130208 (samples) x 3 (bytes) x 8 (channels) x 2 (buffers)
/sbin/modprobe uio_pruss extram_pool_sz=0x800000 #K3

#Enable the PRU
if [ -z `grep BB-BONE-PRU-fs $CAPE_SLOTS` ]; then
	echo "bbb-as startup.sh : Loading the PRU device-tree-overlay ..."
	echo BB-BONE-PRU-fs > $CAPE_SLOTS
fi

#Enable the internal ADC (Kernel 3 only) #K3
echo cape-bone-iio > $CAPE_SLOTS #K3

#Set pin p9.41 to input (allowing me to use it as an input pin)
# p9.41 (CLKOUT2) gpio0[20] corresponds to gpio20
PIN=20
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo in > /sys/class/gpio/gpio$PIN/direction
	echo rising > /sys/class/gpio/gpio$PIN/edge
	chown debian /sys/class/gpio/gpio$PIN/edge
fi

#Set up the input pin for the onboard/offboard recording switch
# p9.41 (GPI03_20) gpio3[20] corresponds to gpio116
PIN=116
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo in > /sys/class/gpio/gpio$PIN/direction
	echo rising > /sys/class/gpio/gpio$PIN/edge
	chown debian /sys/class/gpio/gpio$PIN/edge
fi

#Set pin p9.42 to input (allowing me to use it as a PRU input pin)
# p9.42 (GPIO0_7) gpio0[7] corresponds to gpio7
PIN=7
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo in > /sys/class/gpio/gpio$PIN/direction
fi

#Set up the 3.3V HIGH for the offboard recording switch
# p9.11 (UART4_RXD) gpio0[30] corresponds to gpio30
PIN=30
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo out > /sys/class/gpio/gpio$PIN/direction
	echo 1 > /sys/class/gpio/gpio$PIN/value
	chown debian /sys/class/gpio/gpio$PIN/value
fi

#Set up a pin for turning off the recorder
# p9.13 (UART4_TXD) gpio0[31] corresponds to gpio31
PIN=31
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo out > /sys/class/gpio/gpio$PIN/direction
	echo 0 > /sys/class/gpio/gpio$PIN/value
	chown debian /sys/class/gpio/gpio$PIN/value
fi

#Set up the 3.3V HIGH for ADS1271 J2.12
# p8.46 (GPIO2_7) gpio2[7] corresponds to gpio71
PIN=71
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo out > /sys/class/gpio/gpio$PIN/direction
	echo 1 > /sys/class/gpio/gpio$PIN/value
	chown debian /sys/class/gpio/gpio$PIN/value
fi

#Set up the switch for the ADS1271 power 
# p9.16 (EHRPWM1B) gpio1[19] corresponds to gpio51
#I am using this pin because it is low at boot
PIN=51
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo out > /sys/class/gpio/gpio$PIN/direction
	echo 0 > /sys/class/gpio/gpio$PIN/value
	chown debian /sys/class/gpio/gpio$PIN/value
fi

#Set up the switch for the ADS1271 PSYNC 
# p8.10 (TIMER6) gpio2[4] corresponds to gpio68
PIN=68
if ! [ -d /sys/class/gpio/gpio$PIN/ ]; then
	echo "bbb-as startup.sh : Setting up GPIO pin $PIN"
	echo $PIN > /sys/class/gpio/export
	echo out > /sys/class/gpio/gpio$PIN/direction
	echo 0 > /sys/class/gpio/gpio$PIN/value
	chown debian /sys/class/gpio/gpio$PIN/value
fi

#Start the power_off_fix running #K3
/usr/local/bin/power_off_fix /dev/input/event0 & #K3

echo "bbb-as startup.sh : Starting up wait_to_record"
/usr/local/bin/wait_to_record &

#Update the rtc, if internet time is available
if /usr/sbin/ntpdate 2.debian.pool.ntp.org; then
	echo "bbb-as startup.sh : Resetting the real-time clock"
    hwclock -w -f /dev/rtc1
fi

exit 0
