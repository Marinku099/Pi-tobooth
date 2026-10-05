#include "oscam.h"

int oscam_qbufs(int fd, struct v4l2_requestbuffers *reqbuf) {

    // Put each buffer in queue (waiting for driver to use)
	for (unsigned int i = 0; i < reqbuf->count; i++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));

        // NOTE: Index is just the label for this buffer slot
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		buf.index = i;

        // Error Handler: Failed to put buffers in queue
		if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
			fprintf(stderr, "qbuf index %u is failed: %s\n", i, strerror(errno));
			return -1;
		}
	}

    return 0;
}