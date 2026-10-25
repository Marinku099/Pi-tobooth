#include "oscam.h"

int oscam_streamoff(int fd, enum v4l2_buf_type *type){
    
    // Error Handler: Stream off is failed
    // VIDIOC_STREAMOFF: end the capture stream
	if (ioctl(fd, VIDIOC_STREAMOFF, type) == -1) {
		fprintf(stderr, "Streamoff is failed: %s\n", strerror(errno));
		return -1;
	}

	return 0;
}