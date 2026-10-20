#include "oscam.h"
#include "paths.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <poll.h>
#include <gpiod.h>
#include <signal.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define CHIP_PATH "/dev/gpiochip4"
#define LED_PIN 21
#define BTN_PIN 16

volatile sig_atomic_t keep_running = 1;

void handle_sigint(int sig) {
    signal(sig, SIG_IGN);
    keep_running = 0;
}

int main(void) {

    /* ---------------- Button & LED ----------------------- */
    /*
    signal(SIGINT, handle_sigint);

    // open gpio chip 
    struct gpiod_chip *chip = gpiod_chip_open(CHIP_PATH);
    if (!chip) {
        fprintf(stderr, "gpiod_chip_open failed: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    // led output
    struct gpiod_line_settings *led_settings = gpiod_line_settings_new();
    gpiod_line_settings_set_direction(led_settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(led_settings, GPIOD_LINE_VALUE_INACTIVE);
    */



    /* --------------------- Camera ---------------------------- */
    /*  
        V4L2 capture flow
            1. open (oscam_open)
            2. QUERYCAP + S_FMT (oscam_setformat) 
            3. REQBUFS (oscam_reqbufs)
            4. QUERYBUF + mmap (oscam_querybufs)
            5. QBUF (oscam_qbufs)
            6. STREAMON (oscam_streamom)
            7. รอ signal จากปุ่ม (กำลังทำ) แล้ววนตามจำนวนครั้งที่ถ่าย (1 คลิก 4 ครั้ง)
                poll → DQBUF → เช็กว่ารูปสมบูรณ์ไหม (ถ้าดีแล้วเก็บลง buffer) → QBUF (oscam_capture)
            8. STREAMOFF (oscam_streamoff)
            9. munmap + close (oscam_close)
    */
    
    // Connect to camera
    const char *dev_name = "/dev/v4l/by-id/usb-046d_0825_4555BF00-video-index0";
    const char *raw_dir = getenv("RAW");

    // Get into the working dir (to save picture correctly)
    if(chdir(raw_dir) == -1){
        exit(EXIT_FAILURE);
    }

    int fd = oscam_open(dev_name);
 
    if (fd == -1) {
		exit(EXIT_FAILURE);
	}

    int width = 1280, height = 720;
    struct v4l2_format fmt;
    
    // Set camera size to width * height
    if (oscam_setformat(fd, width, height, V4L2_PIX_FMT_MJPEG, &fmt) == -1) {
		exit(EXIT_FAILURE);
	}

    // Request buffers
    struct v4l2_requestbuffers reqbuf;
    int nbuffer = 4;
    if (oscam_reqbufs(fd, nbuffer, &reqbuf) == -1) {
        exit(EXIT_FAILURE);
    }

    // Mapping logical address (in kernel) with programmer's variables
    struct buffer *buffers = calloc(reqbuf.count, sizeof(*buffers));
    if (oscam_querybufs(fd, buffers, &reqbuf) == -1) {
        exit(EXIT_FAILURE);
    }

    // Push buffers in queue -> waiting for use
    if (oscam_qbufs(fd, &reqbuf) == -1) {
        exit(EXIT_FAILURE);
    }

    // Start video capture
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (oscam_streamon(fd, &type) == -1) {
        exit(EXIT_FAILURE);
    }

    int n_frames = 4;

    // Wait for signal to trigger
    while (1) {
        struct v4l2_buffer buf;

        /*
            ----- Signal handler -----
        */

        // If button pressed -> shoot 4 frames (hope for at least 1 success frame)
        // NOTE: Every frame still in buffers
        for (int frame = 0; frame < n_frames; frame++) {
            if (oscam_capture(fd, buffers, &buf) == -1) {
                continue;
            }   
        }

        // Save one of those success frames
        if (oscam_saveimg_timestramp(fd, buffers, &buf) == -1) {
            fprintf(stderr, "failed to save an image: %s\n", strerror(errno));
            // NOTE: If it cannot save the picture, how can we tell user?
        }
    }

    // Stop camera capture
    if (oscam_streamoff(fd, &type) == -1) {
        exit(EXIT_FAILURE);
    }

    // Free resources
    if (oscam_close(fd, buffers, &reqbuf) == -1) {
        exit(EXIT_FAILURE);
    }

    return 0;
}