// prucode_clk.p
//
// BBB Schematic  BBB port Assign   Bit
// -------------  -------- -------- ------------
// GPIO2_6        P8.45    CLK		PRU1 r30.t0
#define CLK r30.t0

.origin 0
.entrypoint START

#define CONST_PRUCFG         C4
#define CONST_DDR            C31

// Address for the Constant table Programmable Pointer Register 1(CTPPR_1)
#define CTPPR_1         0x2402C

//Register names
#define TEMP_REG1 r0
#define TEMP_REG2 r1
#define CLK_PERIOD r14

//Macros
.macro  DUMMY
    MOV TEMP_REG1, 0
.endm

START:

    // Enable OCP master port
    LBCO	TEMP_REG1, CONST_PRUCFG, 4, 4
    CLR		TEMP_REG1, TEMP_REG1, 4         // Clear SYSCFG[STANDBY_INIT] to enable OCP master port
    SBCO	TEMP_REG1, CONST_PRUCFG, 4, 4

    // Configure the programmable pointer register for PRU0 by setting c31_pointer[15:0]
    // field to 0x0010.  This will make C31 point to 0x80001000 (DDR memory).
    MOV     TEMP_REG1, 0x00100000
    MOV		TEMP_REG2, CTPPR_1
    SBBO    TEMP_REG1, TEMP_REG2, #0x00, 4
    
    LBCO CLK_PERIOD, CONST_DDR, 16, 4 // Get the clock period
    //JMP PERIOD_60_NS
    QBEQ PERIOD_30_NS, CLK_PERIOD, 30
    QBEQ PERIOD_40_NS, CLK_PERIOD, 40
    QBEQ PERIOD_50_NS, CLK_PERIOD, 50
    QBEQ PERIOD_60_NS, CLK_PERIOD, 60
    QBEQ PERIOD_80_NS, CLK_PERIOD, 80

	//Each clock cycle takes 5ns

PERIOD_30_NS:
	//The clock is high for 3 cycles, and low for 3 cycles,
	//giving a clock period of 30ns, and a frequency of 33.3 MHz

	//UP CLOCK 1
    SET CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    
    //DOWN CLOCK
    CLR CLK  // 1 Cycle
    DUMMY  // 1 Cycle
	JMP PERIOD_30_NS // 1 Cycle

PERIOD_40_NS:
	//The clock is high for 4 cycles, and low for 4 cycles,
	//giving a clock period of 40ns, and a frequency of 25 MHz

	//UP CLOCK 1
    SET CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    
    //DOWN CLOCK
    CLR CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
	JMP PERIOD_40_NS // 1 Cycle

PERIOD_50_NS:
	//The clock is high for 5 cycles, and low for 5 cycles,
	//giving a clock period of 50ns, and a frequency of 20 MHz

	//UP CLOCK 1
    SET CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    
    //DOWN CLOCK
    CLR CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
	JMP PERIOD_50_NS // 1 Cycle

PERIOD_60_NS:
	//The clock is high for 6 cycles, and low for 6 cycles,
	//giving a clock period of 60ns, and a frequency of 16.7 MHz

	//UP CLOCK 1
    SET CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    
    //DOWN CLOCK
    CLR CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    JMP PERIOD_60_NS // 1 Cycle

PERIOD_80_NS:
	//The clock is high for 8 cycles, and low for 8 cycles,
	//giving a clock period of 80ns, and a frequency of 12.5 MHz

	//UP CLOCK 1
    SET CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    
    //DOWN CLOCK
    CLR CLK  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    DUMMY  // 1 Cycle
    JMP PERIOD_80_NS // 1 Cycle

