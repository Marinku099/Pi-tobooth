#include "oscam.h"

void oscam_clearbuf(int fd, int count) {
	for (int i=0; i < count; i++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));
		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;
		
		struct pollfd pfd = { .fd = fd, .events = POLLIN };
		if (poll(&pfd, 1, 100) <= 0) break;
		
		if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
			break;
		}
		ioctl(fd, VIDIOC_QBUF, &buf);
		
	}
}
