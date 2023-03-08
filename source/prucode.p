// prucode.p
//
// BBB Schematic  BBB port Assign   Bit
// -------------  -------- -------- ------------
// GPIO1_15       P8.15    DOUT		PRU0 r31.t15
// GPIO1_14       P8.16    DRDY		PRU0 r31.t14
// GPIO3_18       P9.42    RSTOP	PRU0 r31.t4
#define DOUT r31.t15
#define DRDY r31.t14
#define RSTOP r31.t4

.origin 0
.entrypoint START

#define CONST_PRUCFG         C4
#define CONST_DDR            C31

// Address for the Constant table Programmable Pointer Register 0(CTPPR_0)
#define CTPPR_0         0x22028

// Address for the Constant table Programmable Pointer Register 1(CTPPR_1)
#define CTPPR_1         0x2202C

//Global variables
#define READY 0

//Register names

#define TEMP_REG1 r0
#define TEMP_REG2 r1
#define CURRENT_BIT r2 //contains the current bit from the ADCs being written
#define CURRENT_GRAB r3 //contains the number of integers left to be stored in the current buffer
#define BUF_STATE r4 //this register contains the buffer signal to send to the HOST
#define BYTE_BIT r5 // current bit in the register being written
#define SHARED_MEM_POINTER r6 //Pointer to the shared memory location
#define ADC_REG1 r7
#define ADC_REG2 r8
#define ADC_REG3 r9
#define ADC_REG4 r10
#define ADC_REG5 r11
#define ADC_REG6 r12
#define NUM_CHANNELS r13
#define SAMPLES_PER_BUFFER r14
#define SHIFT r15
#define NUM_BUFFERS r16
#define FINISHED r17
#define MEMORY_START_LOCATION r18

//Macros

.macro  DUMMY
    MOV TEMP_REG1, 0
.endm

.macro CLK_30NS
.endm
.macro CLK_40NS
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
.endm
.macro CLK_50NS
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
.endm
.macro CLK_60NS
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
.endm
.macro CLK_80NS
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
    MOV TEMP_REG1, 0
.endm


.macro  WAIT_FOR_BUFFER
DELAY2:
    LBCO TEMP_REG1, CONST_DDR, 0, 4
    QBNE DELAY2, TEMP_REG1, READY
.endm


//If prucode_clk.p is set to run a SPI/ADC clock at a period of 40ns
//(8 clock cycles), in high speed mode, we have a total of 6 x 256 = 1536
//PRU clock cycles between DRDY drops (ie new data points). We need to
//complete ALL operations within this time, including shifting data across
//to the DDR memory.

START: //(I don't care how long this takes, as it is only executed once)

    // Enable OCP master port
    LBCO	TEMP_REG1, CONST_PRUCFG, 4, 4
    CLR		TEMP_REG1, TEMP_REG1, 4         // Clear SYSCFG[STANDBY_INIT] to enable OCP master port
    SBCO	TEMP_REG1, CONST_PRUCFG, 4, 4

    // Configure the programmable pointer register for PRU0 by setting c28_pointer[15:0]
    // field to 0x0100.  This will make C28 point to 0x00010000 (PRU shared RAM).
    MOV     TEMP_REG1, 0x00000100
    MOV     TEMP_REG2, CTPPR_0
    SBBO    TEMP_REG1, TEMP_REG2, #0x00, 4

    // Configure the programmable pointer register for PRU0 by setting c31_pointer[15:0]
    // field to 0x0010.  This will make C31 point to 0x80001000 (DDR memory).
    MOV     TEMP_REG1, 0x00100000
    MOV		TEMP_REG2, CTPPR_1
    SBBO    TEMP_REG1, TEMP_REG2, #0x00, 4

    MOV BUF_STATE, 1
    
    LBCO NUM_CHANNELS, CONST_DDR, 8, 4 // Get the number of channels
    LBCO SAMPLES_PER_BUFFER, CONST_DDR, 12, 4 // Get the grab length
    LBCO SHIFT, CONST_DDR, 20, 4 // Get the SHIFT_CHANNEL flag
    LBCO NUM_BUFFERS, CONST_DDR, 24, 4 // Get the number of buffers flag
    ADD FINISHED, NUM_BUFFERS, 1 // finished should now contain (num_buffers + 1)
    
	LBCO MEMORY_START_LOCATION, CONST_DDR, 4, 4
    MOV SHARED_MEM_POINTER, MEMORY_START_LOCATION
       
//This is the beginning of the buffer loop. This loop runs through once to fill
//the first buffer, then once again to fill the second buffer, and then it goes
//back to the first buffer etc.
BUF_START: //(1 Clock Cycle)
    MOV CURRENT_GRAB, SAMPLES_PER_BUFFER 

//This is the beginning of the data loop. This loop runs through until
//a buffer is filled.
SPI_GRAB: //(8 Clock Cycles + Wait time)

    MOV CURRENT_BIT, 32 
    MOV ADC_REG1, 0
    MOV ADC_REG2, 0
    MOV ADC_REG3, 0
    MOV ADC_REG4, 0
    MOV ADC_REG5, 0
    MOV ADC_REG6, 0
	WBC DRDY // wait for DRDY falling edge
	// We now have 8 clock cycles to get each bit from the ADCs
	
GRAB_ADC_VALUES: //(6 x 24 x 8(channels) = 6 x 32 x 6(registers) = 1152 clock cycles)

REG6:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG6_SET, DOUT // CLOCK CYCLE 2
	JMP REG6_NEXT // CLOCK CYCLE 3
REG6_SET:
	SET ADC_REG6, CURRENT_BIT // CLOCK CYCLE 3
REG6_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ REG6_DONE, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG6 //CLOCK CYCLE 6
REG6_DONE:
    MOV CURRENT_BIT, 32 //CLOCK CYCLE 6
    
REG5:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG5_SET, DOUT // CLOCK CYCLE 2
	JMP REG5_NEXT // CLOCK CYCLE 3
REG5_SET:
	SET ADC_REG5, CURRENT_BIT // CLOCK CYCLE 3
REG5_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ REG5_DONE, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG5 //CLOCK CYCLE 6
REG5_DONE:
    MOV CURRENT_BIT, 32 //CLOCK CYCLE 6
    
REG4:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG4_SET, DOUT // CLOCK CYCLE 2
	JMP REG4_NEXT // CLOCK CYCLE 3
REG4_SET:
	SET ADC_REG4, CURRENT_BIT // CLOCK CYCLE 3
REG4_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ REG4_DONE, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG4 //CLOCK CYCLE 6
REG4_DONE:
    MOV CURRENT_BIT, 32 //CLOCK CYCLE 6
    
REG3:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG3_SET, DOUT // CLOCK CYCLE 2
	JMP REG3_NEXT // CLOCK CYCLE 3
REG3_SET:
	SET ADC_REG3, CURRENT_BIT // CLOCK CYCLE 3
REG3_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ REG3_DONE, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG3 //CLOCK CYCLE 6
REG3_DONE:
    MOV CURRENT_BIT, 32 //CLOCK CYCLE 6
    
REG2:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG2_SET, DOUT // CLOCK CYCLE 2
	JMP REG2_NEXT // CLOCK CYCLE 3
REG2_SET:
	SET ADC_REG2, CURRENT_BIT // CLOCK CYCLE 3
REG2_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ REG2_DONE, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG2 //CLOCK CYCLE 6
REG2_DONE:
    MOV CURRENT_BIT, 32 //CLOCK CYCLE 6
    
REG1:
	SUB CURRENT_BIT, CURRENT_BIT, 1 // CLOCK CYCLE 1
	QBBS REG1_SET, DOUT // CLOCK CYCLE 2
	JMP REG1_NEXT // CLOCK CYCLE 3
REG1_SET:
	SET ADC_REG1, CURRENT_BIT // CLOCK CYCLE 3
REG1_NEXT:
    DUMMY // CLOCK CYCLE 4
    CLK_PERIOD_ALIAS
    QBEQ GOT_DATA, CURRENT_BIT, 0 // CLOCK CYCLE 5
    JMP REG1 //CLOCK CYCLE 6
    

GOT_DATA: //(Approx 132 Clock Cycles)
    
    //We have finished getting one set of samples from the ADCs
    
    //Let's see if we are shifting the channels
    QBEQ CHANNEL_SHIFT, SHIFT, 1 // 1 CYCLE

    //Let's see how many channels we are recording
    QBEQ EIGHT_CHANNEL, NUM_CHANNELS, 8 // 1 Cycle
    QBEQ SEVEN_CHANNEL, NUM_CHANNELS, 7 // 1 Cycle
    QBEQ SIX_CHANNEL,   NUM_CHANNELS, 6 // 1 Cycle
    QBEQ FIVE_CHANNEL,  NUM_CHANNELS, 5 // 1 Cycle
    QBEQ FOUR_CHANNEL,  NUM_CHANNELS, 4 // 1 Cycle
    QBEQ THREE_CHANNEL, NUM_CHANNELS, 3 // 1 Cycle
    QBEQ TWO_CHANNEL,   NUM_CHANNELS, 2 // 1 Cycle
    QBEQ ONE_CHANNEL,   NUM_CHANNELS, 1 // 1 Cycle

EIGHT_CHANNEL:
    //Send 8 channels, ie 24 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 24 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 24
    JMP COPY_FINISHED
SEVEN_CHANNEL:
    //Send 7 channels, ie 21 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 21 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 21
    JMP COPY_FINISHED
SIX_CHANNEL:
    //Send 6 channels, ie 18 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 18 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 18
    JMP COPY_FINISHED
FIVE_CHANNEL:
    //Send 5 channels, ie 15 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 15 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 15
    JMP COPY_FINISHED
FOUR_CHANNEL:
    //Send 4 channels, ie 12 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 12 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 12
    JMP COPY_FINISHED
THREE_CHANNEL:
    //Send 3 channels, ie 9 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 9 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 9
    JMP COPY_FINISHED
TWO_CHANNEL:
    //Send 2 channels, ie 6 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 6 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 6
    JMP COPY_FINISHED
ONE_CHANNEL:
    //Send 1 channels, ie 3 bytes to the Shared Ram)
    SBBO ADC_REG1, SHARED_MEM_POINTER, 0, 3 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 3
    JMP COPY_FINISHED

CHANNEL_SHIFT:
    //Let's see how many channels we are recording
    QBEQ EIGHT_CHANNEL, NUM_CHANNELS, 8 // 1 Cycle
    QBEQ SEVEN_CHANNEL_SHIFT, NUM_CHANNELS, 7 // 1 Cycle
    QBEQ SIX_CHANNEL_SHIFT,   NUM_CHANNELS, 6 // 1 Cycle
    QBEQ FIVE_CHANNEL_SHIFT,  NUM_CHANNELS, 5 // 1 Cycle
    QBEQ FOUR_CHANNEL_SHIFT,  NUM_CHANNELS, 4 // 1 Cycle
    QBEQ THREE_CHANNEL_SHIFT, NUM_CHANNELS, 3 // 1 Cycle
    QBEQ TWO_CHANNEL_SHIFT,   NUM_CHANNELS, 2 // 1 Cycle
    QBEQ ONE_CHANNEL_SHIFT,   NUM_CHANNELS, 1 // 1 Cycle

SEVEN_CHANNEL_SHIFT:
    //Send 7 channels, ie 21 bytes to the Shared Ram)
    SBBO ADC_REG1.b3, SHARED_MEM_POINTER, 0, 21 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 21
    JMP COPY_FINISHED
SIX_CHANNEL_SHIFT:
    //Send 6 channels, ie 18 bytes to the Shared Ram)
    SBBO ADC_REG2.b2, SHARED_MEM_POINTER, 0, 18 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 18
    JMP COPY_FINISHED
FIVE_CHANNEL_SHIFT:
    //Send 5 channels, ie 15 bytes to the Shared Ram)
    SBBO ADC_REG3.b1, SHARED_MEM_POINTER, 0, 15 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 15
    JMP COPY_FINISHED
FOUR_CHANNEL_SHIFT:
    //Send 4 channels, ie 12 bytes to the Shared Ram)
    SBBO ADC_REG4, SHARED_MEM_POINTER, 0, 12 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 12
    JMP COPY_FINISHED
THREE_CHANNEL_SHIFT:
    //Send 3 channels, ie 9 bytes to the Shared Ram)
    SBBO ADC_REG4.b3, SHARED_MEM_POINTER, 0, 9 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 9
    JMP COPY_FINISHED
TWO_CHANNEL_SHIFT:
    //Send 2 channels, ie 6 bytes to the Shared Ram)
    SBBO ADC_REG5.b2, SHARED_MEM_POINTER, 0, 6 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 6
    JMP COPY_FINISHED
ONE_CHANNEL_SHIFT:
    //Send 1 channels, ie 3 bytes to the Shared Ram)
    SBBO ADC_REG6.b1, SHARED_MEM_POINTER, 0, 3 // Approx ?? Clock cycles
    ADD SHARED_MEM_POINTER, SHARED_MEM_POINTER, 3
    JMP COPY_FINISHED

COPY_FINISHED:    
	SUB CURRENT_GRAB, CURRENT_GRAB, 1
    QBNE SPI_GRAB, CURRENT_GRAB, 0 

SWITCH_BUFFER: //(A max of 143 clock cycles)
	// This is the end of the loop which fills an individual buffer.

	// Check if the stop button has been pushed
	QBBC DONT_STOP, RSTOP // Keep going unless button is set
	MOV BUF_STATE, FINISHED
    SBCO BUF_STATE, CONST_DDR, 0, 4 // (43 Clock cycles)
    HALT  // HALT the PRU

DONT_STOP:
	// Wait for the host to zero the buffer state
	WAIT_FOR_BUFFER // (44 Clock cycles)
    // Let the host know that the buffer is ready to be recorded
    SBCO BUF_STATE, CONST_DDR, 0, 4 // (43 Clock cycles)
    
    //Now I need to increment the buffer state
    ADD BUF_STATE, BUF_STATE, 1
    QBNE BUF_START, BUF_STATE, FINISHED // If we are not at the end of the buffer ring, then get another buffer
    
    //We are at the end of the buffer, so set it back to the first buffer
    //And set the shared memory point back to the beginning.
	MOV BUF_STATE, 1
    MOV SHARED_MEM_POINTER, MEMORY_START_LOCATION
	JMP BUF_START
	
