#include "oscam.h"

int oscam_capture(int fd, struct buffer *buffers, struct v4l2_buffer *buf) {

	struct pollfd pfd;
	pfd.fd = fd;
	pfd.events = POLLIN;
	
	memset(buf, 0, sizeof(*buf));

	buf->type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf->memory = V4L2_MEMORY_MMAP;

	// NOTE: Poll is for waiting input data (from Webcam) in limited time
	// Poll return -1: poll error, it's a function error
	// Poll return 0: poll timeout, it's wait more than WAIT_TIME and still no input data
	// Poll return >0: poll success, it's recieve input data
	int ret = poll(&pfd, 1, WAIT_TIME);

	if (ret == -1) { // Error Handler: poll function error
		fprintf(stderr, "poll error: %s\n", strerror(errno));
		return -1;
	} else if (ret == 0) { // Error Handler: timeout, frame is not return in time (WAIT_TIME)
		fprintf(stderr, "timeout: no frame return\n");
		return -1; 
	} else { // Recieve input data
		// Error Handler: Cannot dequeue this buffer
		if (ioctl(fd, VIDIOC_DQBUF, buf) == -1) {
			fprintf(stderr, "dqbuf at this frame is failed: %s\n", strerror(errno));
			return -1;
		}
	}

	// Frame incomplete: its flag mark as error
	if (buf->flags & V4L2_BUF_FLAG_ERROR) {
		fprintf(stderr, "Broken frame (bytesused=%u)\n", buf->bytesused);
		ioctl(fd, VIDIOC_QBUF, buf);
		return -1;  
	}

	// Save image as jpg (use timestramp as file name)
	oscam_saveimg_timestramp(fd, buffers, &buf);

	// Put buffer back to queue
	if (ioctl(fd, VIDIOC_QBUF, buf) == -1) {
		fprintf(stderr, "QBUF (requeue) failed: %s\n", strerror(errno));
		return -1;
	}

	return 0;
}