#
# Execute 'make' to create prucode.bin, prucode_clk.p, acquire_data and wait_to_record
# Other options:
# make clean
# make all
# make pru
# make project
# make prucode
# make clean
#

pru = prucode prucode_clk
project = acquire_data wait_to_record power_off_fix get_binary

LIB_PATH = /usr/local/lib
LIBRARIES = pthread prussdrv
INCLUDES = -I. ${LIB_PATH}

SOURCES =  acquire_data.c

EXTRA_DEFINE = -D_FILE_OFFSET_BITS=64 -DNUM_BITS=24 -DCLK_PERIOD_ALIAS=CLK_30NS
CCCFLAGS = $(EXTRA_DEFINE)
CC = gcc
CFLAGS = $(EXTRA_DEFINE)
PASM = pasm

all : $(pru) $(project)
pru : $(pru)
project: $(project)

$(project) : $(project:%=%.c)
	$(CC) $(CFLAGS) -c -o $@.o $@.c
	$(CC) $@.o $(LIB_PATH:%=-L%) $(LIBRARIES:%=-l%) -o $@

clean :
	rm -rf *.o *.bin $(project) core *~

$(pru) : $(pru:%=%.p)
	$(PASM) -b $@.p $(EXTRA_DEFINE)

.SUFFIXES: .c.d

%.d: %.c
	$(SHELL) -ec "$(CC) -M $(CPPFLAGS) $< | sed 's/$*\\.o[ :]*/$@ &/g' > $@" -include $(SOURCES:.c=.d)

