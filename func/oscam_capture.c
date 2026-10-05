#include "oscam.h"

int oscam_capture(int fd, int n_frames, struct buffer *buffers) {

    // reuse elements
    int hours, minutes, seconds, day, month, year;

    // loop by frame
	for (int frame = 0; frame < n_frames; frame++) {
		struct v4l2_buffer buf;
		memset(&buf, 0, sizeof(buf));

		buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
		buf.memory = V4L2_MEMORY_MMAP;

        // Error Handler: Cannot dequeue this buffer
		if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
			fprintf(stderr, "dqbuf at frame %d is failed: %s\n", frame, strerror(errno));
			return -1;
		}

        // Get current timestamp
        time_t now = time(NULL);
        struct tm *local = localtime(&now);
 
        hours = local->tm_hour;         // get hours since midnight (0-23)
        minutes = local->tm_min;        // get minutes passed after the hour (0-59)
        seconds = local->tm_sec;        // get seconds passed after a minute (0-59)
    
        day = local->tm_mday;            // get day of month (1 to 31)
        month = local->tm_mon + 1;      // get month of year (0 to 11)
        year = local->tm_year + 1900;

        // Set filename in format "capture_<date>_<time>.jpg"
        char filename[64];
		snprintf(filename, sizeof(filename), "capture_%02d%02d%04d_%02d%02d%02d.jpg", day, month, year, hours, minutes, seconds);

        // save file
		FILE *fp = fopen(filename, "wb");
		if (fp == NULL) {
			fprintf(stderr, "cannot open file %s: %s\n", filename, strerror(errno));
		} else {
			fwrite(buffers[buf.index].start, buf.bytesused, 1, fp);
			fclose(fp);
			printf("save %s\n", filename);
		}

        // put buffer back to queue
		if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
			fprintf(stderr, "QBUF (requeue) failed: %s\n", strerror(errno));
			return -1;
		}
	}
	return 0;
}