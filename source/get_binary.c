/* 
 * get_binary.c
 * 
******************************************************************************/

// Standard header files
#include <stdio.h>
#include <stdlib.h> 

#define BUFFER_MAX 130208 

int main (int argc, char **argv)
{
	unsigned long long mem_start = atoll(argv[2]);
	long long count = atoll(argv[3]);
	long long block = atoll(argv[4]);
	
	char buffer[BUFFER_MAX];
	FILE *fp = fopen( argv[1], "rb" );
	fseeko(fp, mem_start, SEEK_SET);
	long long i;

	if (argc > 5) {
		printf("mem_start = %lld, count = %lld, block = %lld, output file = %s\n",mem_start,count,block,argv[5]);
		FILE *fout = fopen( argv[5], "wb" );
		for (i = 0; i<count; i = i + block) { 
			fread(buffer, 1, block, fp);
			fwrite(buffer, 1, block, fout);
		}
		fclose(fout);    
	} else {
		for (i = 0; i<count; i = i + block) { 
			fread(buffer, 1, block, fp);
			fwrite(buffer, 1, block, stdout);    
		}
	}
    
    fclose(fp);
    
    return(0);
    
}

