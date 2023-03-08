/*
 * retrieve_data.c
 * 
 * This program attempts to retrieve data after a PRU crash.
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

/******************************************************************************
* Global Variable Definitions                                                 *
******************************************************************************/

#define SAMPLE_LENGTH 1024
// GRAB_LENGTH - Number of samples in each buffer
// NUM_BITS - Number of bits per sample
// NUM_CHANNELS - Number of channels to be recorded
// FILE_MEM - The memory device being copied from

/******************************************************************************
* Global Function Definitions                                                 *
******************************************************************************/

int main (int argc, char **argv)
{

	int i = atoi(argv[2]);
	int ret = -1;

	long long big_bytes = (long long)NUM_CHANNELS*(long long)3*(long long)GRAB_LENGTH*(long long)i;
	printf("INFO: Files size is %lld bytes\n",big_bytes);
	if ( big_bytes < 2147479552 )
	{
		size_t fsize = NUM_CHANNELS*3*GRAB_LENGTH*i;
		size_t size_to_send;
		int in_file;
		int out_file;

		printf("INFO: Using sendfile to copy binary to SD directory.\r\n");
		printf("INFO: Opening the temporary output device %s.\r\n", FILE_MEM);
		printf("INFO: Opening the binary output device %s.\r\n", argv[1]);
		fflush(stdout);
		in_file = open(FILE_MEM, O_RDONLY);
		out_file = open(argv[1], O_WRONLY | O_CREAT | O_TRUNC, 0644);

		off_t offset = 0;
		for (size_to_send = fsize; size_to_send > 0; )
		{
			ssize_t sent = sendfile(out_file, in_file, &offset, size_to_send);
			if (sent <= 0)
			{
				if (sent != 0)
					perror("sendfile");
				break;
			}
			offset += sent;
			size_to_send -= sent;	
		}
		printf("INFO: Closing the temporary output device %s.\r\n", FILE_MEM);
		printf("INFO: Closing the binary output device %s.\r\n", argv[1]);
		fflush(stdout);
		close(in_file);
		close(out_file);

	} else
	{
		printf("INFO: Using buffer to copy binary to SD directory.\r\n");
		printf("INFO: Opening the temporary output device %s.\r\n",  FILE_MEM);
		fflush(stdout);
		FILE *fp = fopen( FILE_MEM, "rb" );
		if ( fp == 0 )
		{
			printf( "Could not open the device\n" );
			fflush(stdout);
			return (ret);
		}
	 
		printf("INFO: Opening the binary output file %s.\r\n",  argv[1]);
		fflush(stdout);
		FILE *fp_binary = fopen( argv[1], "wb" );
		if ( fp_binary == 0 )
		{
			printf( "Could not open file\n" );
			fflush(stdout);
			return (ret);
		}
	
		int k;
		unsigned char buff[NUM_CHANNELS*3*GRAB_LENGTH];
		for (k = 0; k<i; k++)
		{
			fread(buff,1, sizeof buff,fp);
			fwrite(buff,1, sizeof buff,fp_binary);
		} 
   
		printf("INFO: Closing the temporary output device %s.\r\n", FILE_MEM);
		fflush(stdout);
		fclose(fp);
		
		printf("INFO: Closing the binary output file %s.\r\n", argv[1]);
		fflush(stdout);
		fclose(fp_binary);

	}
	
	
    return(0);
    
}

