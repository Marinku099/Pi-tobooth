#include "oscam.h"

int oscam_capture(int fd, struct buffer *buffers, struct v4l2_buffer *buf)
{

	struct pollfd pfd;
	pfd.fd = fd;
	pfd.events = POLLIN;

	// struct v4l2_buffer buf;
	memset(buf, 0, sizeof(*buf));

	buf->type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
	buf->memory = V4L2_MEMORY_MMAP;

	int ret = poll(&pfd, 1, 3000);

	// Error Handler: Cannot dequeue this buffer
	if (ioctl(fd, VIDIOC_DQBUF, buf) == -1)
	{
		fprintf(stderr, "dqbuf at this frame is failed: %s\n", strerror(errno));
		return -1;
	}

	// put buffer back to queue

	return 0;
}