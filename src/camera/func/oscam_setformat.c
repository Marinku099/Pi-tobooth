#include "oscam.h"

int oscam_setformat(int fd, int width, int height, __u32 pixfmt, struct v4l2_format *out_fmt) {

    // Clear garbage memory  
    memset(out_fmt, 0, sizeof(*out_fmt));

    // Set v4l2_format for pictures format
    out_fmt->type                   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    out_fmt->fmt.pix.width          = width;
    out_fmt->fmt.pix.height         = height;
    out_fmt->fmt.pix.pixelformat    = pixfmt;
    out_fmt->fmt.pix.field          = V4L2_FIELD_NONE;

    // Error Handler: Cannot set these format to camera 
    if (ioctl(fd, VIDIOC_S_FMT, out_fmt) == -1) {
            fprintf(stderr, "S_FMT size %dx%d failed: %s\n",
                    width, height, strerror(errno));
            // Return failed status
            return -1;
    }

    // Return success status
    return 0;
}