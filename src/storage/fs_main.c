#include "fs_manager.h"
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

int main(){ 
    
    setvbuf(stdout, NULL, _IOLBF, 0);

    printf("start fs_main\n");
    
    int init = fs_init(getenv("PHOTOBOOTH_DIR"));
    if(init==0){
        printf("init succesfully\n");
    }

    for(;;){
        sleep(3);
        printf("running fs....");
    }
    return 0;
}