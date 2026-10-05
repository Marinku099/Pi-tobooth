#include "oscam.h"

int oscam_open(const char *cam_name) {
    // --- Open Camera ---

	// Open Camera
	// O_RDWR is just an open flag
	int fd = open(cam_name, O_RDWR);

	// Error Handler: Camera failed to open
	if (fd == -1) {
		fprintf(stderr, "Failed to open %s: %s\n", cam_name, strerror(errno));
		return -1;
	}
	
	// Specification of Camera
	struct v4l2_capability cap;
	memset(&cap, 0, sizeof(cap)); // set every bytes to 0 (clear garbage)

	// Error Handler: VIDIOC_QUERYCAP failed to open
	if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
		fprintf(stderr, "Failed to query camera capabilities (VIDIOC_QUERYCAP): %s\n", strerror(errno));
		close(fd);
		return -1;
	}

    // Error Handler: Device is not support video capture
    if (!(cap.device_caps & V4L2_CAP_VIDEO_CAPTURE)) {
		fprintf(stderr, "%s is not support Video Capture\n", cam_name);
        close(fd);
        return -1;
	}

    return fd;
}