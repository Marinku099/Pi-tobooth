#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define MAX_SIZES 32

struct buffer {
	void *start;
	size_t length;
};

int main(void) {
	// --- Open Camera ---

	// Camera name (depend on user device)
	//const char *dev_name = "/dev/video0";

	// Camera name by-id
	const char *dev_name = "/dev/v4l/by-id/usb-046d_0825_4555BF00-video-index0"; 

	// Open Camera
	// O_RDWR is just an open flag
	int fd = open(dev_name, O_RDWR);

	// Error Handler: Camera failed to open
	if (fd == -1) {
		fprintf(stderr, "Failed to open %s: %s\n", dev_name, strerror(errno));
		exit(EXIT_FAILURE);
	}

	struct pollfd pfd;
	pfd.fd = fd;
	pfd.events = POLLIN;
	
	// Specification of Camera
	struct v4l2_capability cap;
	memset(&cap, 0, sizeof(cap)); // set every bytes to 0 (clear garbage)

	// Error Handler: VIDIOC_QUERYCAP failed to open
	if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
		fprintf(stderr, "Failed to query camera capabilities (VIDIOC_QUERYCAP): %s\n", strerror(errno));
		close(fd);
		exit(EXIT_FAILURE);
	}

	// Show data from VIDIOC_QUERYCAP
	printf("driver: %s\n", cap.driver);
	printf("card: %s\n", cap.card);
	printf("bus_info: %s\n", cap.bus_info);
	printf("device_caps: 0x%08x\n", cap.device_caps);

	// Check if the camera support Video Capture (Can it capture a photo?)
	if (cap.device_caps & V4L2_CAP_VIDEO_CAPTURE) {
		printf("support Video Capture\n");
	}
	else {
		printf("NOT support Video Capture\n");
	}

	
	
	// --- Check Image Sizes ---

	struct { int width, height; } sizes[MAX_SIZES];
	int n_sizes = 0;

	struct v4l2_frmsizeenum frmsize;
	memset(&frmsize, 0, sizeof(frmsize));
	frmsize.pixel_format = V4L2_PIX_FMT_MJPEG;
	frmsize.index = 0;

	while (ioctl(fd, VIDIOC_ENUM_FRAMESIZES, &frmsize) == 0 && n_sizes < MAX_SIZES) {
		if (frmsize.type == V4L2_FRMSIZE_TYPE_DISCRETE) {
		/*	printf("size #%d: %ux%u\n",
					frmsize.index,
					frmsize.discrete.width,
					frmsize.discrete.height); */
			sizes[n_sizes].width = frmsize.discrete.width;
			sizes[n_sizes].height = frmsize.discrete.height;
			n_sizes++;
		}
		frmsize.index++;
	}

	printf("\nfound %d sizes\n", n_sizes);

	for (int i = 0; i < n_sizes; i++) {
		struct v4l2_format fmt;
		memset(&fmt, 0, sizeof(fmt));

		fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		fmt.fmt.pix.width = sizes[i].width;
		fmt.fmt.pix.height = sizes[i].height;
		fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;
		fmt.fmt.pix.field = V4L2_FIELD_NONE;

		if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
        		fprintf(stderr, "S_FMT size %dx%d failed: %s\n",
                		sizes[i].width, sizes[i].height, strerror(errno));
			continue;
		}

		printf("successful set %dx%d -> real image size %ux%u, sizeimage= %u bytes (%.1f KB)\n",
           		sizes[i].width, sizes[i].height,
           		fmt.fmt.pix.width, fmt.fmt.pix.height, fmt.fmt.pix.sizeimage, fmt.fmt.pix.sizeimage/1024.0);

		// --- Request buffer for Images ---
		
		// VIDIOC_REQBUFS for initiate memory mapping
		struct v4l2_requestbuffers reqbuf;
		memset(&reqbuf, 0, sizeof(reqbuf));

		reqbuf.count = 4;
		reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		reqbuf.memory = V4L2_MEMORY_MMAP;

		if (ioctl(fd, VIDIOC_REQBUFS, &reqbuf) == -1) {
			fprintf(stderr, "VIDIOC_REQBUFS failed: %s\n", strerror(errno));
			exit(EXIT_FAILURE);
		}

		printf("driver set to %u buffers\n", reqbuf.count);

		struct buffer *buffers = calloc(reqbuf.count, sizeof(*buffers));

		if (buffers == NULL) {
			fprintf(stderr, "calloc failed for %u buffers\n", reqbuf.count);
			exit(EXIT_FAILURE);
		}
		printf("calloc ok, buffers = %p\n", (void *)buffers);
		
		for (unsigned int j = 0; j < reqbuf.count; j++) {
			struct v4l2_buffer buf;
			memset(&buf, 0, sizeof(buf));

			buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
			buf.memory = V4L2_MEMORY_MMAP;
			buf.index = j;

			if (ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
				fprintf(stderr, "QUERYBUF index %u is failed: %s\n", j, strerror(errno));
				exit(EXIT_FAILURE);
			}

			buffers[j].length = buf.length;
			buffers[j].start = mmap(NULL, buf.length, 
									PROT_READ | PROT_WRITE, MAP_SHARED, fd, buf.m.offset);

			if (buffers[j].start == MAP_FAILED) {
				fprintf(stderr, "mmap index %u is failed: %s\n", j, strerror(errno));
				exit(EXIT_FAILURE);
			}
		}

		for (unsigned int j = 0; j < reqbuf.count; j++) {
			struct v4l2_buffer buf;
			memset(&buf, 0, sizeof(buf));

			buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
			buf.memory = V4L2_MEMORY_MMAP;
			buf.index = j;

			if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
				fprintf(stderr, "qbuf index %u is failed: %s\n", j, strerror(errno));
				exit(EXIT_FAILURE);
			}
		}

		enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

		if (ioctl(fd, VIDIOC_STREAMON, &type) == -1) {
			fprintf(stderr, "Streamon is failed: %s\n", strerror(errno));
			exit(EXIT_FAILURE);
		}

		int n_frames = 4;

		for (int frame = 0; frame < n_frames; frame++) {
			struct v4l2_buffer buf;
			memset(&buf, 0, sizeof(buf));

			buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
			buf.memory = V4L2_MEMORY_MMAP;

			int ret = poll(&pfd, 1, 3000);   // รอสูงสุด 3000 ms (3 วินาที)

			if (ret == -1) {
				fprintf(stderr, "poll error: %s\n", strerror(errno));
				exit(EXIT_FAILURE);
			} else if (ret == 0) {
				fprintf(stderr, "timeout: ไม่มีเฟรมมาใน 3 วินาที ข้ามเฟรมนี้\n");
				continue; 
			} else {
				if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
					fprintf(stderr, "dqbuf at frame %d is failed: %s\n", frame, strerror(errno));
					exit(EXIT_FAILURE);
				}
			}

			if (buf.flags & V4L2_BUF_FLAG_ERROR) {
				fprintf(stderr, "เฟรมเสีย (bytesused=%u) ข้ามไป\n", buf.bytesused);
				ioctl(fd, VIDIOC_QBUF, &buf);
				continue;   // กลับไปรอเฟรมถัดไป ไม่เขียนไฟล์เฟรมนี้
			}

			printf("At frame %d: buffer index=%u, byteused=%d\n", frame, buf.index, buf.bytesused);


			
			char filename[64];
			snprintf(filename, sizeof(filename), "capture_%dx%d.jpg", sizes[i].width, sizes[i].height);
			FILE *fp = fopen(filename, "wb");
			if (fp == NULL) {
				fprintf(stderr, "cannot open file %s: %s\n", filename, strerror(errno));
			} else {
				fwrite(buffers[buf.index].start, buf.bytesused, 1, fp);
				fclose(fp);
				printf("save %s\n", filename);
			}

			if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
				fprintf(stderr, "QBUF (requeue) failed: %s\n", strerror(errno));
				exit(EXIT_FAILURE);
			}
		}

		if (ioctl(fd, VIDIOC_STREAMOFF, &type) == -1) {
			fprintf(stderr, "Streamoff is failed: %s\n", strerror(errno));
			exit(EXIT_FAILURE);
		}

		for (unsigned int j = 0; j < reqbuf.count; j++) {
			munmap(buffers[j].start, buffers[j].length);
		}

		free(buffers);

		memset(&reqbuf, 0, sizeof(reqbuf));
		reqbuf.count  = 0;
		reqbuf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		reqbuf.memory = V4L2_MEMORY_MMAP;

		if (ioctl(fd, VIDIOC_REQBUFS, &reqbuf) == -1) {
			fprintf(stderr, "REQBUFS(0) cleanup failed: %s\n", strerror(errno));
			exit(EXIT_FAILURE);
		}

		usleep(500000);
	}
	
	close(fd);
	return 0;
}