#!/bin/bash
for i in 30 40 50 60 80; do
    cp prucode.p prucode_${i}.p
    pasm -b prucode_${i}.p -D_FILE_OFFSET_BITS=64 -DCLK_PERIOD_ALIAS=CLK_${i}NS
    rm prucode_${i}.p
done
pasm -b prucode_clk.p 

gcc -D_FILE_OFFSET_BITS=64 -DNUM_BITS=24 -c -o acquire_data.o acquire_data.c
gcc acquire_data.o -L/usr/local/lib -lpthread -lprussdrv -o acquire_data
gcc -D_FILE_OFFSET_BITS=64 -DNUM_BITS=24 -c -o data_to_ram.o data_to_ram.c
gcc data_to_ram.o -L/usr/local/lib -lfftw3 -lm -lpthread -lprussdrv -o data_to_ram
gcc -D_FILE_OFFSET_BITS=64 -c -o wait_to_record.o wait_to_record.c
gcc wait_to_record.o -L/usr/local/lib -lpthread -lprussdrv -o wait_to_record
gcc -D_FILE_OFFSET_BITS=64 -c -o power_off_fix.o power_off_fix.c
gcc power_off_fix.o -L/usr/local/lib -lpthread -lprussdrv -o power_off_fix
gcc -D_FILE_OFFSET_BITS=64 -c -o get_binary.o get_binary.c
gcc get_binary.o -L/usr/local/lib -lpthread -lprussdrv -o get_binary
