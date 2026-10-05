#ifndef OSCAM_H
#define OSCAM_H

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define MAX_SIZES 32

struct buffer {
	void *start;
	size_t length;
};

int oscam_open(const char *cam_name);
int oscam_setformat(int fd, int width, int height, __u32 pixfmt, struct v4l2_format *out_fmt);
int oscam_reqbufs(int fd, int nbuffers, struct v4l2_requestbuffers *reqbuf);
int oscam_querybufs(int fd, struct buffer *buffers, struct v4l2_requestbuffers *reqbuf);
int oscam_qbufs(int fd, struct v4l2_requestbuffers *reqbuf);
int oscam_streamon(int fd, enum v4l2_buf_type *type);
int oscam_capture(int fd, int n_frames, struct buffer *buffers);
int oscam_streamoff(int fd, enum v4l2_buf_type *type);
int oscam_close(int fd, struct buffer *buffers, struct v4l2_requestbuffers *reqbuf);

#endif