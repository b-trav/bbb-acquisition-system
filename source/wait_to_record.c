#include <stdio.h> 
#include <stdlib.h> 
#include <fcntl.h>
#include <sys/select.h>

#define MAX_BUF 64 
#define DEFAULT_BUTTON 20 // p9.41 (CLKOUT2) gpio0[20] corresponds to gpio20
#define DEFAULT_POWER 51 // p9.16 (EHRPWM1B) gpio1[19] corresponds to gpio51

int main(int argc, char **argv) { 
		
	int len; 
	char *buf[MAX_BUF];
	char button[MAX_BUF];
	snprintf(button, sizeof button, "%s%d%s", "/sys/class/gpio/gpio", DEFAULT_BUTTON, "/value");
	char power[MAX_BUF];
	snprintf(power, sizeof power, "%s%d%s", "/sys/class/gpio/gpio", DEFAULT_POWER, "/value");
	int fd;
	fd_set exceptfds;
	int res;
	char but_ch = '0';
	FILE *f_button;

	while ( 1 ) {
		fd = open(button, O_RDONLY); 
		FD_ZERO(&exceptfds); 
		FD_SET(fd, &exceptfds);
		len = read(fd, buf, MAX_BUF);//won't work without this read.
		res = select(fd+1, 
		 NULL, // readfds - not needed 
		 NULL, // writefds - not needed
		 &exceptfds, 
		 NULL);// timeout (never)

		if (res > 0 && FD_ISSET(fd, &exceptfds)) {
			printf("bbb-as wait_to_record : Recording button has been pushed\n");
			f_button = fopen(power,"r");
			but_ch = fgetc(f_button);
			fclose(f_button);
			if( but_ch == '1' ) {
				printf("bbb-as wait_to_record : recorder appears to already be running.\n");				
			} else {
                if( access( "/tmp/octaves", F_OK ) != -1 ) {
                    //If start_recording.py is not already running, then start it.
                    system("/usr/local/bin/start_analysing.py >/var/log/bbbas/recording &");                  
                } else {
                    //If start_recording.py is not already running, then start it.
                    system("/usr/local/bin/start_recording.py >/var/log/bbbas/recording &");
                }
			}
			
		}
		usleep(10000000);//Sleep for 10 seconds
	}
	return 0;
}
