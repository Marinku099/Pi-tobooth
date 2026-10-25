#include "oscam.h"

int oscam_reqbufs(int fd, int nbuffers, struct v4l2_requestbuffers *reqbuf) {

    // Clear garbage memory
    memset(reqbuf, 0, sizeof(*reqbuf));

    // Set v4l2_requestbuffers
    // count -> number of buffer requested; more buffer reduce the chance of dropped frames
    // NOTE: 4 is just fine for taking a shot
	reqbuf->count = nbuffers;
	reqbuf->type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	reqbuf->memory = V4L2_MEMORY_MMAP;

    // VIDIOC_REQBUFS: reserved memory for buffers (in kernel space)
    // Error Handler: Failed to request buffers
	if (ioctl(fd, VIDIOC_REQBUFS, reqbuf) == -1) {
		fprintf(stderr, "VIDIOC_REQBUFS failed: %s\n", strerror(errno));
		// return failed status
        return -1;
	}

    // return success status
    return 0;
}