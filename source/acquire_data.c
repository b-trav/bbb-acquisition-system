/*
 * acquire_data.c
 * 
 * This program uses the two PRUs on the beaglebone black to record data
 * from up to eight analog channels using four ADS1271EVMs.
 * 
 * This program is not designed to be executed directly by the user.
 * It is executed by a python helper program called "start_recording.py"
 * 
 */

/******************************************************************************
* Include Files                                                               *
******************************************************************************/

// Standard header files
#include <stdio.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <string.h>
#include <linux/fs.h>
#include <stdlib.h>
#include <sched.h>
#include <sys/time.h>
#include <netdb.h>
#include <sys/socket.h>
#include <netinet/in.h>
 
// Driver header files
#include "prussdrv.h"
#include <pruss_intc_mapping.h>	 

/******************************************************************************
* Local Macro Declarations                                                    *
******************************************************************************/

#define BUFLEN 128  //Max length of UDP buffer

#define PRU_NUM_0 	 0
#define PRU_NUM_1 	 1

#define DDR_BASEADDR     0x80000000
#define OFFSET_DDR	 0x00001000 

#define READY 0
#define PRU_LIMIT 10000000

#define POWER 51 // p9.16 (EHRPWM1B) gpio1[19] corresponds to gpio51
#define PSYNC 68 // p8.10 (TIMER6) gpio2[4] corresponds to gpio68


/******************************************************************************
* Global Variable Definitions                                                 *
******************************************************************************/

#define SAMPLE_LENGTH 1024
// NUM_BITS - Number of bits per sample

/******************************************************************************
* Global Function Definitions                                                 *
******************************************************************************/
int set_button(int, int);

int set_button(int pin, int value)
{
	char gpio[200];

	snprintf(gpio, sizeof gpio, "%s%d%s", "/sys/class/gpio/gpio", pin, "/value");
	FILE *f = fopen( gpio, "rb+" );
	if ( f == 0 )
	{
		printf( "Could not set %s to %d\n",  gpio, value);
		fflush(stdout);
        return (-1);
	}
	fprintf(f, "%d", value);
	fclose(f);
	return 0;
}

void die(char *s)
{
    perror(s);
    exit(1);
}

int main (int argc, char **argv)
{
	//UDP stuff
	struct sockaddr_in si_me, si_other;
     
    int sock, mesg_len, slen = sizeof(si_other);
    char udp_buf[BUFLEN];	

	//create a UDP socket
    if ((sock=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        die("socket");
    }
    
    char hostname[15];
    char portnum[5];
	if (argc > 4) {
		snprintf(hostname, sizeof hostname, argv[4]);
	}
	if (argc > 5) {
		snprintf(portnum, sizeof portnum, argv[5]);
	}

	struct addrinfo hints;
	memset(&hints,0,sizeof(hints));
	hints.ai_family=AF_UNSPEC;
	hints.ai_socktype=SOCK_DGRAM;
	hints.ai_protocol=0;
	hints.ai_flags=AI_ADDRCONFIG;
	struct addrinfo* res=0;
	int err=getaddrinfo(hostname,portnum,&hints,&res);
	if (err!=0) {
		die("failed to resolve remote socket address");
	}
	
	//Return value
	unsigned int ret = -1;
	
	// PRU/Linux Memory addresses and pointers
    void *DDR_regaddr1;
  	static int mem_fd;
	static void *ddrMem, *ERam;
	static char * ERam_char;
    unsigned int ESize, EOffs;
    tpruss_intc_initdata pruss_intc_initdata = PRUSS_INTC_INITDATA;
	const char *file_mem = "/dev/mmcblk0p2";
	//const char *file_mem = "/dev/sda1";
	const char *linux_share = "/dev/shm/bbbas";
	const char *mem_start_filename = "/mnt/externalSD/.mem_start";
	char pru_clock_executable[100];
	char pru_acquire_executable[100];
	
	int num_seconds; // The number of seconds to be recorded
	int num_bytes = (long long)NUM_BITS/(long long)8;
	long long mem_start; //The offset for /dev/mmcblk0p2
	long long mem_size; //The amount of /dev/mmcblk0p2 memory used for the recording
	int sample_rate;
	int num_channels;
	int clk_period;
    int shift_channels = 0;

    printf("INFO: Opening the memory offset file %s.\r\n",  mem_start_filename);
    fflush(stdout);
	FILE *f_mem_start = fopen( mem_start_filename, "r" );
	if ( f_mem_start == 0 )
	{
		printf( "Could not open the memory offset file %s.\r\n",  mem_start_filename);
		fflush(stdout);
        return (ret);
	}
	fscanf (f_mem_start, "%lld", &mem_start);
	fclose(f_mem_start);

    printf("INFO: Opening the binary storage memory %s.\r\n",  file_mem);
    fflush(stdout);
	FILE *fp = fopen( file_mem, "wb" );
	if ( fp == 0 )
	{
		printf( "Could not open the binary storage memory\n" );
		fflush(stdout);
        return (ret);
	}

	if (argc > 2) {
		sample_rate = atoi(argv[2]);
	} else {
		//Using the maximum sample rate:
		sample_rate = 130208;
	}
	switch (sample_rate) {
		case 130208 :
			clk_period = 30;
			break;
		case 97656 :
			clk_period = 40;
			break;
		case 78125 :
			clk_period = 50;
			break;
		case 65104 :
			clk_period = 60;
			break;
		case 48828 :
			clk_period = 80;
			break;
		default :
			printf("\npERROR: Please enter a valid sample rate.\n");
			fflush(stdout);
			return (ret);		
	}
		
	if (argc > 3) {
		num_channels = atoi(argv[3]);
	} else {
		//Using the maximum number of channels:
		num_channels = 8;
	}
    if (  (num_channels > 8) || (num_channels < 1) ) {
        printf("\nERROR: Please enter a valid number of channels.\n");
        fflush(stdout);
        return (ret);
    }

    if (argc > 6) {
        shift_channels = 1;
        printf("\nINFO: Channels are being shifted\n");
        fflush(stdout);
    }
    
	unsigned long long binary_file_space;
	ioctl(fileno(fp), BLKGETSIZE64, &binary_file_space);
	num_seconds = (int) ((binary_file_space-mem_start)/(num_bytes * (long long) sample_rate * (long long) num_channels)) - 1;
	printf("INFO: There are %lld bytes in %s, starting at %lld, we have %lld free bytes\nINFO: We can record for a maximum of %d seconds.\n",binary_file_space,file_mem,mem_start,binary_file_space-mem_start,num_seconds);
	fflush(stdout);
	
	if (argc > 1) {
		num_seconds = ((num_seconds) < (atoi(argv[1])) ? num_seconds : atoi(argv[1]));
	}
	
	int num_buffers = 2;
	int finished = num_buffers + 1;
	const int external_mem_size = 8388608;
	//int samples_per_buffer = (external_mem_size/num_buffers) / (num_bytes * num_channels);
	int samples_per_buffer = sample_rate;
	int buffer_size = (num_bytes * num_channels) * samples_per_buffer ;
	int num_grabs = (int) ( ( (long long) num_seconds * (long long) sample_rate )/ (long long) samples_per_buffer ) ;
    printf("INFO: Grabbing a maximum of %d seconds of data.\n",num_seconds);
    printf("INFO: Each buffer is %d bytes, which contains %d samples.\n",buffer_size, samples_per_buffer);
    printf("INFO: Each sample contains %d x %d = %d bytes.\n",num_channels,num_bytes,num_channels * num_bytes);
    printf("INFO: Grabbing %d buffers equates to %f seconds.\n",num_grabs,(float) num_grabs * (float) samples_per_buffer / (float) sample_rate);
    fflush(stdout);
	
	fseeko(fp, mem_start, SEEK_SET);

    printf("INFO: Opening the shared RAM for python: %s.\r\n",  linux_share);
    fflush(stdout);
	FILE *RAM_file = fopen( linux_share, "wb" );
	if ( RAM_file == 0 )
	{
		printf( "Could not open the shared RAM for python\n" );
		fflush(stdout);
        return (ret);
	}

    printf("INFO: Starting the PRU/ADC program\n");
    fflush(stdout);
    /* Initialize the PRU */
    prussdrv_init ();		
    
    // Open PRU0 Interrupt
    ret = prussdrv_open(PRU_EVTOUT_0);
    if (ret)
    {
        printf("\nprussdrv_open open failed\n");
		fflush(stdout);
        return (ret);
    }
    
    // Open PRU1 Interrupt
    ret = prussdrv_open(PRU_EVTOUT_1);
    if (ret)
    {
        printf("\nprussdrv_open open failed\n");
		fflush(stdout);
        return (ret);
    }
    
    // Get the interrupt initialized
    prussdrv_pruintc_init(&pruss_intc_initdata);

    // open the device
    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd < 0) {
        printf("Failed to open /dev/mem (%s)\n", strerror(errno));
		fflush(stdout);
        return -1;
    }	

    // map the DDR memory
    ddrMem = mmap(0, 0x0FFFFFFF, PROT_WRITE | PROT_READ, MAP_SHARED, mem_fd, DDR_BASEADDR);
    if (ddrMem == NULL) {
        printf("Failed to map the device (%s)\n", strerror(errno));
		fflush(stdout);
        close(mem_fd);
        return -1;
    }
    DDR_regaddr1 = ddrMem + OFFSET_DDR;
    unsigned int *DDR_int_ptr = (unsigned int*) DDR_regaddr1;
    
 	prussdrv_map_extmem(&ERam);
 	ESize = prussdrv_extmem_size();
 	EOffs = prussdrv_get_phys_addr(ERam);
	printf("\tINFO: Size of external memory : %d\n",ESize);
    fflush(stdout);
	ERam_char = (char *) ERam;
    
    DDR_int_ptr[0] = READY; 
    DDR_int_ptr[1] = EOffs;
    DDR_int_ptr[2] = num_channels; //This int (register) holds to number of channels
    DDR_int_ptr[3] = samples_per_buffer; //This  int (register) holds the samples per buffer
    DDR_int_ptr[4] = clk_period; //This int (register) holds the clock period
    DDR_int_ptr[5] = shift_channels; //This int (register) holds the channel shift flag
    DDR_int_ptr[6] = num_buffers; //This int (register) holds the number of buffers
    
	printf("\tINFO: Initial DDR State : %d\n",DDR_int_ptr[0]);
 	printf("\tINFO: Number of channels being recorded : %d\n",DDR_int_ptr[2]);
 	printf("\tINFO: Sample per buffer: %d\n",DDR_int_ptr[3]);
 	printf("\tINFO: Sample rate: %d\n",sample_rate);
 	printf("\tINFO: Clock period (ns): %d\n",DDR_int_ptr[4]);
    fflush(stdout);

	// Set the POWER line to high
    printf("\tINFO: Powering up the ADCs\r\n");
    fflush(stdout);
    set_button(POWER,1);
	
	// Wait for ADC to settle
	usleep(500000);

    // Start the clock running on PRU1
	snprintf(pru_clock_executable, sizeof pru_clock_executable, "./prucode_clk.bin");
	printf("\tINFO: Executing the clock %s code on PRU1.\r\n",pru_clock_executable);
    fflush(stdout);
	prussdrv_exec_program (PRU_NUM_1, pru_clock_executable);

	// Set the PSYNC line to high
    printf("\tINFO: Turning on the ADCs\r\n");
    fflush(stdout);
    set_button(PSYNC,1);
	
	// Wait for ADC to settle
	usleep(10000);

    // Start recording data on PRU0 
	snprintf(pru_acquire_executable, sizeof pru_acquire_executable, "./prucode_%d.bin", clk_period);
    printf("\tINFO: Executing data gathering code %s on PRU0.\r\n",pru_acquire_executable);
    fflush(stdout);
    prussdrv_exec_program (PRU_NUM_0, pru_acquire_executable);

	struct sched_param param;
	param.sched_priority = 98;
	if (sched_setscheduler(0, SCHED_FIFO,& param) == 0 )
		{
		printf("INFO: acquire_data program has maximum priority\n");
		fflush(stdout);			
		}

    int i = 0; //Counter used to measure number of buffer grabs recorded.
    int pru_check = 0; // Counter to determine if the PRU has crashed
    int buffer_number = 0; // Which buffer to write from
    long buffer_time = (long) samples_per_buffer / (long) sample_rate * 1000000;
    struct timeval start, end;
    long micros_used, secs_used;
    unsigned int timestamp;
    int num_drops = 0;
    int drop_packet[100];
    int drop_time[100];
    int k;
    while ( ( i < num_grabs ) && ( DDR_int_ptr[0] != finished ) && (pru_check < PRU_LIMIT) )
    {
		if ( ( DDR_int_ptr[0] != READY ) || ( DDR_int_ptr[0] == finished ))
		{
			gettimeofday(&start, NULL); // Start measuring the time
			buffer_number = DDR_int_ptr[0] - 1; 
			fwrite(&ERam_char[buffer_number*buffer_size], buffer_size, 1, fp);    
			DDR_int_ptr[0] = READY;
            fflush(fp);
			i++;
			pru_check = 0;
            gettimeofday(&end, NULL); //Stop measuring the time
            secs_used=(end.tv_sec - start.tv_sec); //avoid overflow by subtracting first
            micros_used= ((secs_used*1000000) + end.tv_usec) - (start.tv_usec);
            timestamp = (unsigned)time(NULL);
            mesg_len = snprintf(udp_buf, sizeof udp_buf, "[%d %d %d %d]", i,num_grabs,timestamp,(int) (buffer_time-micros_used));
            sendto(sock, udp_buf, mesg_len, 0, (struct sockaddr*) res->ai_addr,res->ai_addrlen);
			//printf("grab %d took %d u-secs, leaving %d u-secs spare\n",i,(int) micros_used,(int) (buffer_time-micros_used));
            if ( (micros_used >= buffer_time) && (num_drops < 100) ) {
				drop_packet[num_drops] = i;
				drop_time[num_drops] = timestamp;
				num_drops++;
				//printf("At %u grab %d took %d u-secs, which is %d u-secs too long!\n",(unsigned)time(NULL),i,(int)micros_used,(int) (micros_used-buffer_time));
			} 
			//fwrite(&ERam_char[buffer_size*buffer_size], num_channels*num_bytes*SAMPLE_LENGTH, 1, RAM_file);
			//fseek ( RAM_file , 0 , SEEK_SET );
		}
		else
		{
			pru_check++;
		}
	}
    if (pru_check >= PRU_LIMIT)
    {
		printf("\tERROR: PRUs appear to have frozen after %d seconds.\r\n",i);
		fflush(stdout);
	}
	
	if (num_drops > 0) { //Write the packets and times that were dropped
		FILE *DROP_file = fopen( "/tmp/bbbas_drops", "wb" );
		for (k = 0; k < num_drops; k++) {
			fprintf(DROP_file,"%d:%d,",drop_packet[k],drop_time[k]);
		}
		fclose(DROP_file);	
	} 

	float exact_record_length = (float) i * (float) samples_per_buffer / (float) sample_rate;
    printf("INFO: We Grabbed %d buffers equating to %f seconds.\n",i,exact_record_length);
    printf("INFO: Rounding down to the nearest second.\n");
    int record_length = (int) exact_record_length;
	mem_size = (long long) record_length * num_bytes * (long long) num_channels * (long long) sample_rate;
    printf("INFO: Finished acquiring %d seconds of data, using approximately %lld MB.\r\n",record_length,mem_size/(1024*1024));
    fflush(stdout);

	mesg_len = snprintf(udp_buf, sizeof udp_buf, "Finished");
	sendto(sock, udp_buf, mesg_len, 0, (struct sockaddr*) res->ai_addr,res->ai_addrlen);

	f_mem_start = fopen( mem_start_filename, "w" );
	if ( f_mem_start == 0 )
	{
		printf( "Could not open the memory offset file %s.\r\n",  mem_start_filename);
		fflush(stdout);
        return (ret);
	}
	fprintf(f_mem_start, "%lld\n", mem_start + mem_size);
	fclose(f_mem_start);
	
	//Set the PSYNC line to low
	set_button(PSYNC,0);
	// Turn off power to the ADC 
	set_button(POWER,0);
   
    printf("INFO: Closing the binary storage memory %s.\r\n", file_mem);
    fflush(stdout);
    fclose(fp);
    
	printf("INFO: Closing the python RAM file %s.\r\n", linux_share);
	fflush(stdout);
	fclose(RAM_file);

    // Disable PRUs and close memory mapping
    prussdrv_pru_clear_event (PRU_EVTOUT_0, PRU0_ARM_INTERRUPT);
    prussdrv_pru_disable(PRU_NUM_0); 
    prussdrv_pru_clear_event (PRU_EVTOUT_1, PRU1_ARM_INTERRUPT);
    prussdrv_pru_disable(PRU_NUM_1); 
    
    prussdrv_exit ();

	close(sock); //Close the UDP socket
    
    return(0);
    
}
