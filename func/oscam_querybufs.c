#include "oscam.h"

int oscam_querybufs(int fd, struct buffer *buffers, struct v4l2_requestbuffers *reqbuf){
    
    // Query each buffer's size/location, then map it into our address space via mmap
    for (unsigned int i = 0; i < reqbuf->count; i++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));

        // NOTE: Index is just the label for this buffer slot
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		buf.index = i;

        // Error Handler: Failed to query this buffer
		if (ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
			fprintf(stderr, "QUERYBUF index %u is failed: %s\n", i, strerror(errno));
			return -1;
		}

        // Store this buffer's length and mmap (address of the starting point) for later use
		buffers[i].length = buf.length;
		buffers[i].start = mmap(NULL, buf.length, 
								PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);

        // Error Handler: Failed to mapping space
		if (buffers[i].start == MAP_FAILED) {
			fprintf(stderr, "mmap index %u is failed: %s\n", i, strerror(errno));
			return -1;
		}
	}

    return 0;
}