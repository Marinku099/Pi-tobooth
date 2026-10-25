#include "oscam.h"

int oscam_streamon(int fd, enum v4l2_buf_type *type) {

    // Error Handler: Stream on is failed
    // VIDIOC_STREAMON: start the capture stream
    if (ioctl(fd, VIDIOC_STREAMON, type) == -1) {
		fprintf(stderr, "Streamon is failed: %s\n", strerror(errno));
	    return -1;
	}

    return 0;
}