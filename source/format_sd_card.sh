#!/bin/bash

START1=`cat /sys/block/mmcblk0/mmcblk0p1/start`
SIZE=`cat /sys/block/mmcblk0/size`
SIZE1=$(( 100 * 2048 )) # 100 MB for the fat32 partition
START2=$(( $START1 + $SIZE1 ))
SIZE2=$(( $SIZE - $START1 - $SIZE1 )) 

FDISK_IN="# partition table of /dev/mmcblk0
unit: sectors

/dev/mmcblk0p1 : start= $START1, size= $SIZE1, Id= b
/dev/mmcblk0p2 : start= $START2, size= $SIZE2, Id=83
/dev/mmcblk0p3 : start=        0, size=        0, Id= 0
/dev/mmcblk0p4 : start=        0, size=        0, Id= 0
"
umount -v /mnt/externalSD/
printf '%s\n' "$FDISK_IN" > fdisk.tmp
/sbin/sfdisk /dev/mmcblk0 <fdisk.tmp
rm fdisk.tmp
/sbin/mkfs.msdos -F 32 /dev/mmcblk0p1
/sbin/mkfs.ext4 /dev/mmcblk0p2
mount -v /mnt/externalSD/
cp /home/debian/bbb-acquisition-system/source/view_recordings.py /mnt/externalSD/.
cp /home/debian/bbb-acquisition-system/source/convert_flac.py /mnt/externalSD/.
