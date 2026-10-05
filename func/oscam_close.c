#include "oscam.h"

int oscam_close(int fd, struct buffer *buffers, struct v4l2_requestbuffers *reqbuf) {

    // Unmapping memory
    for (unsigned int i = 0; i < reqbuf->count; i++) {
		munmap(buffers[i].start, buffers[i].length);
	}

    // Free memory and close file decription
	free(buffers);
	close(fd);
}