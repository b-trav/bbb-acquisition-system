#!/bin/bash
# -*- coding: utf-8 -*-
#
#  install.sh
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

INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_SCRIPT=$INSTALL_DIR/`basename "$0"`
DEBIAN_HOME=/home/debian
cd $INSTALL_DIR

log_heading () {
	date
	echo `head -\$((\$1-2)) $INSTALL_SCRIPT | tail -1 | cut -c 3-` ...
	return 0
}

# ----------------------------------------------------------------------
# This program installs the software necessary to use a beaglebone black
# as a data acquisition system, with the ADS1271EVM board as the
# analog-to-digital converter.
#
# This installation script assumes a fresh install of debian linux on a 
# beaglebone black with a working internet connection.
# If this is not the case, then please read the instructions in the
# README.md file contained in this directory.
# ----------------------------------------------------------------------
head -$(($LINENO-1)) $INSTALL_SCRIPT | tail -n11

# ----------------------------------------------------------------------
# Checking that we are running on a beaglebone black
# ----------------------------------------------------------------------
log_heading $LINENO
arch=$(uname -m)
if [ "x${arch}" != "xarmv7l" ]; then
	echo "This machine is a : $arch"
	echo "!!! This machine does not appear to be a beaglebone ! "
	echo "Exiting the installation script. (Check the README.md)"
	exit -1
fi

# ----------------------------------------------------------------------
# Checking that we running as root
# ----------------------------------------------------------------------
log_heading $LINENO
USER=`whoami`
if [[ $USER != 'root' ]]; then
	echo "This script is running as $USER"
	echo "Please use the command : "
	echo "    sudo $INSTALL_SCRIPT"
	exit -1
fi

# ----------------------------------------------------------------------
# Getting the kernel number 
# ----------------------------------------------------------------------
log_heading $LINENO
KERNEL=`uname -r | cut -c 1`

# ----------------------------------------------------------------------
# Adding /mnt/externalSD to fstab 
# ----------------------------------------------------------------------
log_heading $LINENO
if [[ $(grep mmcblk0p1 /etc/fstab) ]]; then
    echo "mmcblk0p1 is already mounted"
else
	mkdir /mnt/externalSD
    echo "/dev/mmcblk0p1 /mnt/externalSD auto auto,user,exec,rw,async,noatime,nofail,umask=0000 0 0" >> /etc/fstab
    mount -a
fi

# ----------------------------------------------------------------------
# Format the SD card for use with bbbas 
# ----------------------------------------------------------------------
log_heading $LINENO
$INSTALL_DIR/source/format_sd_card.sh

# ----------------------------------------------------------------------
# Checking the internet connection
# ----------------------------------------------------------------------
log_heading $LINENO
ping -c 2 google.com
rc=$?
if [[ $rc != 0 ]]; then
	echo "There does not appear to be a working internet connection."
	echo "Exiting the installation script. (Check the README.md)"
	exit -1
fi

# ----------------------------------------------------------------------
# Checking the debian password
# ----------------------------------------------------------------------
log_heading $LINENO
PASS_SALT=`cat /etc/shadow | grep debian | cut -c 8-20`
if [[ $PASS_SALT == 'rcdjoac1gVi9g' ]]; then
	echo "The password is still set to the default."
	echo "Please change it now : "
	passwd debian
fi

# ----------------------------------------------------------------------
# Fixing the eth0 bug
# ----------------------------------------------------------------------
log_heading $LINENO
sed -i 's/auto eth0/allow-hotplug eth0/' /etc/network/interfaces

# ----------------------------------------------------------------------
# Enable backports in wheezy
# ----------------------------------------------------------------------
log_heading $LINENO
file=/etc/apt/sources.list
sed -i 's/^#\(deb .*backport.*\)/\1/' $file


# ----------------------------------------------------------------------
# Updating the package manager
# ----------------------------------------------------------------------
log_heading $LINENO
apt-get update
apt-get -y upgrade

# ----------------------------------------------------------------------
# Installing some packages
# ----------------------------------------------------------------------
log_heading $LINENO
apt-get -y install build-essential python python-cffi python-pip python3 python-dev wpasupplicant git flac ntpdate apache2 php5 device-tree-compiler locales dkms wireless-regdb iw crda vim wireless-tools i2c-tools lsb-release usbutils firmware-ralink pkg-config libzmq-dev libsndfile1 libogg-dev libvorbis-dev libflac-dev libfreetype6-dev libpng-dev libfftw3-dev

# ----------------------------------------------------------------------
# Removing ntpd
# ----------------------------------------------------------------------
log_heading $LINENO
service ntp stop
update-rc.d -f ntp remove

# ----------------------------------------------------------------------
# Configuring the locale and timezone
# ----------------------------------------------------------------------
log_heading $LINENO
if [[ `date | grep UTC` ]]; then
	dpkg-reconfigure locales
	dpkg-reconfigure tzdata
	locale > /etc/locale.conf
fi

# ----------------------------------------------------------------------
# Set the clock (so that git doesn't fail with ssl)
# ----------------------------------------------------------------------
log_heading $LINENO
/usr/sbin/ntpdate 2.debian.pool.ntp.org

# ----------------------------------------------------------------------
# Installing python packages
# ----------------------------------------------------------------------
log_heading $LINENO
pip install -U pip
rm /usr/bin/pip
ln -s  /usr/local/bin/pip /usr/bin/pip
pip install pysoundfile
pip install MarkupSafe
pip install functools32
pip install terminado
date;echo "About to install numpy. This takes a very long time!"
pip install numpy #This takes a very long time!
date;echo "numpy is now installed"
pip install bokeh
pip install jupyter
if [ ! -f $DEBIAN_HOME/.jupyter/jupyter_notebook_config.py ]; then
	su -c "jupyter notebook --generate-config" debian
	sed -i "s/# c\.NotebookApp\.ip = 'localhost'/c.NotebookApp.ip = '*'/" $DEBIAN_HOME/.jupyter/jupyter_notebook_config.py 
fi

# ----------------------------------------------------------------------
# Configuring uEnv.txt
# ----------------------------------------------------------------------
log_heading $LINENO
if [[ $KERNEL == "4" ]]; then
	echo "Disabling HDMI"
	sed -i 's/#\(dtb=am335x-boneblack-emmc-overlay\.dtb\)/\1/' /boot/uEnv.txt
	echo "Disabling universal cape"
	sed -i 's/\(cmdline=coherent_pool=1M quiet\) cape_universal=enable/\1/' /boot/uEnv.txt
else
	echo "Disabling HDMI"
	sed -i 's/#\(cape_disable=capemgr\.disable_partno=BB-BONELT-HDMI,BB-BONELT-HDMIN\)\s*$/\1/' /boot/uEnv.txt
fi

if [[ $KERNEL == "4" ]]; then
	# ----------------------------------------------------------------------
	# Enabling the internal ADC
	# ----------------------------------------------------------------------
	log_heading $LINENO
	# Taken from:
	# https://gist.github.com/matthewmcneely/bf44655c74096ff96475
	cd $DEBIAN_HOME
	ln -s /usr/bin/dtc /usr/local/bin/dtc
	su -c "git clone https://github.com/RobertCNelson/dtb-rebuilder.git" debian
	cd dtb-rebuilder/
	git checkout 4.1.x
	git checkout -- src/arm/am335x-boneblack-emmc-overlay.dts
	cat >> src/arm/am335x-boneblack-emmc-overlay.dts << EOM
	
&tscadc {
    status = "okay";
};

&am335x_adc {
    ti,adc-channels = <0 1 2 3 4 5 6 7>;
};

&pruss {
	status = "okay";
};

EOM
	chown debian:debian src/arm/am335x-boneblack-emmc-overlay.dts
	make all
	cp src/arm/am335x-boneblack-emmc-overlay.dtb /boot/dtbs/*/.
	cd $DEBIAN_HOME
fi

# ----------------------------------------------------------------------
# Installing the pru code
# ----------------------------------------------------------------------
log_heading $LINENO
if [ ! -f $DEBIAN_HOME/am335x_pru_package/README.txt ]; then
	cd $DEBIAN_HOME
	su -c "git clone https://github.com/beagleboard/am335x_pru_package.git" debian
	cd am335x_pru_package
	su -c make debian
	make install
	#Get rid of the shared libraries, forcing the code to use static ones
	rm /usr/local/lib/libprussdrv*.so
	cd $DEBIAN_HOME
fi

# ----------------------------------------------------------------------
# Building the acquisition system code
# ----------------------------------------------------------------------
log_heading $LINENO
cd $INSTALL_DIR/source
make clean
su -c ./make.sh debian

# ----------------------------------------------------------------------
# Install various executables
# ----------------------------------------------------------------------
log_heading $LINENO
cd $INSTALL_DIR/source
ln -s $INSTALL_DIR/source/check_voltage.py /usr/local/bin/check_voltage.py
pkill wait_to_record
ln -s $INSTALL_DIR/source/wait_to_record /usr/local/bin/wait_to_record
ln -s $INSTALL_DIR/source/get_binary /usr/local/bin/get_binary
ln -s $INSTALL_DIR/source/start_recording.py /usr/local/bin/start_recording.py
ln -s $INSTALL_DIR/source/start_analysing.py /usr/local/bin/start_analysing.py
ln -s $INSTALL_DIR/source/convert_flac.py /usr/local/bin/convert_flac.py
ln -s $INSTALL_DIR/source/bbbas_powerdown.py /usr/local/bin/bbbas_powerdown.py
if [[ $KERNEL == "3" ]]; then
	ln -s $INSTALL_DIR/source/power_off_fix /usr/local/bin/power_off_fix
fi

# ----------------------------------------------------------------------
# Removing excess lines from startup.sh
# ----------------------------------------------------------------------
log_heading $LINENO
cd $INSTALL_DIR
if [[ $KERNEL == "4" ]]; then
	sed -i '/#K3/d' startup.sh
else
	sed -i '/#K4/d' startup.sh
fi

# ----------------------------------------------------------------------
# Building the PRU DeviceTreeOverlay
# ----------------------------------------------------------------------
log_heading $LINENO
dts_file="$INSTALL_DIR/source/BB-BONE-PRU-fs-00A0.dts"
if [[ $KERNEL == "4" ]] && [[ `grep pruss $dts_file` ]]; then
	# ----------------------------------------------------------------------
	# Removing PRU stuff from DTO (doesn't currently work in kernel 4)
	# ----------------------------------------------------------------------
	echo `head -$(($LINENO-2)) $INSTALL_SCRIPT | tail -1 | cut -c 3-` ... 
	sed -i -e '56,68d' $dts_file	
fi
dtc -O dtb -o /lib/firmware/BB-BONE-PRU-fs-00A0.dtbo -b 0 -@ $dts_file

if [[ $KERNEL == "4" ]]; then
	# ----------------------------------------------------------------------
	# Installing the uio_pruss
	# ----------------------------------------------------------------------
	echo `head -$(($LINENO-2)) $INSTALL_SCRIPT | tail -1 | cut -c 3-` ... 
	echo "TODO: The PRU cape is still not working in kernel 4"
	cd $DEBIAN_HOME
	su -c "git clone https://github.com/izaakschroeder/uio_pruss.git uio_pruss" debian
	apt-get install linux-headers-$(uname -r)
	sed -i 's/\(static int extram_pool_sz =\) SZ_256K;/\1 SZ_8M;/' uio_pruss/uio_pruss.c
	dkms add uio_pruss
	dkms install uio_pruss/3.18.0
	modprobe uio_pruss	
fi


# ----------------------------------------------------------------------
# Adding check_voltage to root's crontab
# ----------------------------------------------------------------------
log_heading $LINENO
cronline="*/1 * * * * /usr/local/bin/check_voltage.py"
if [ -z "`crontab -l | grep check_voltage`" ]; then
	(crontab -l; echo "$cronline" ) | crontab -
fi

# ----------------------------------------------------------------------
# Checking to see if we have a real-time clock
# ----------------------------------------------------------------------
log_heading $LINENO
if [[ $KERNEL == "4" ]]; then
	i2cdetect -y -r 2
else
	i2cdetect -y -r 1
fi

# ----------------------------------------------------------------------
# Getting ifup to run dhclient
# ----------------------------------------------------------------------
log_heading $LINENO
dhclient_script="/etc/network/if-up.d/zz_dhclient"
				cat > $dhclient_script <<EOM
#!/bin/bash
WLAN=\`ifconfig -a | grep wlan | awk '{print \$1;}'\`
logger "bbb-as: running zz_dhclient"
dhclient -x -pf /run/dhclient.\$WLAN.pid
dhclient -nw -v -pf /run/dhclient.\$WLAN.pid -lf /var/lib/dhcp/dhclient.\$WLAN.leases \$WLAN
EOM
chmod +x $dhclient_script

# ----------------------------------------------------------------------
# Setting up the /etc/rc.local file
# ----------------------------------------------------------------------
log_heading $LINENO
cd $INSTALL_DIR
cp source/rc.local /etc/.

# ----------------------------------------------------------------------
# Create a log directory for bbbas
# ----------------------------------------------------------------------
log_heading $LINENO
mkdir /var/log/bbbas

# ----------------------------------------------------------------------
# Configuring webserver
# ----------------------------------------------------------------------
log_heading $LINENO
a2enmod rewrite
systemctl stop apache2.service
apache_file=/etc/apache2/sites-enabled/000-default
sed -i 's/\/var\/www/\/home\/debian\/bbb-acquisition-system\/web/g' $apache_file
sed -i 's/AllowOverride None/AllowOverride All/g' $apache_file
apache_file=/etc/apache2/envvars
sed -i 's/APACHE_RUN_USER=www-data/APACHE_RUN_USER=debian/' $apache_file
sed -i 's/APACHE_RUN_GROUP=www-data/APACHE_RUN_GROUP=debian/' $apache_file
sed -i 's/^\(export LANG=C\)/#\1/' $apache_file
sed -i 's/^#\(\. \/etc\/default\/locale\)/\1/' $apache_file
systemctl start apache2.service


# ----------------------------------------------------------------------
# Configuring the wifi
# ----------------------------------------------------------------------
log_heading $LINENO
if [[ ! `grep wpa-conf /etc/network/interfaces` ]]; then
	echo "  Configuring /etc/network/interfaces ..."
	cat >> /etc/network/interfaces << EOM

# Added by bbb-acquisition-system:
allow-hotplug wlan0
iface wlan0 inet manual
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

# Added by bbb-acquisition-system:
allow-hotplug wlan1
iface wlan1 inet manual
wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
EOM
fi 

$INSTALL_DIR/configure_wifi.py

USB_IP=`ifconfig usb0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`

echo ""
echo ""
echo "==================================================================="
echo "  The installation should be complete."
echo "  Please re-boot the Beaglebone Black with the command:"
echo
echo "  sudo reboot;exit;exit"
echo
echo "  After reboot go to the ip address of your Beaglebone Black:"
echo "  in a browser to access the acquisition system GUI."
echo
echo "     usb ip  : $USB_IP"
echo
echo "  To find the wifi ip address either consult your router or "
echo "  log in over usb and type:"
echo "      sudo ifconfig -a"
echo
echo "==================================================================="


