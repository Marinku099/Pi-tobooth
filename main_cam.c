#include "oscam.h"
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

#define CHIP_PATH "/dev/gpiochip4" // NOTE: MUST recheck with real environment

volatile sig_atomic_t keep_running = 1;

void handle_sigint(int sig) {
    signal(sig, SIG_IGN);
    keep_running = 0;
}

struct gpiod_hw {
    struct gpiod_line_request *request;
    unsigned int offset;
};

int led_config(const char *chip_path, const unsigned int *offsets, int count, struct gpiod_hw *out_leds) {

    // open gpio chip 
    struct gpiod_chip *chip = gpiod_chip_open(CHIP_PATH);
    if (!chip) {
        fprintf(stderr, "gpiod_chip_open failed: %s\n", strerror(errno));
        return -1;
    }

    // led output
    struct gpiod_request_config *led_req_cfg = gpiod_request_config_new();
    gpiod_request_config_set_consumer(led_req_cfg, "oscam-led");

    for (int i = 0; i < count; i++) {
        struct gpiod_line_settings *led_settings = gpiod_line_settings_new();
        gpiod_line_settings_set_direction(led_settings, GPIOD_LINE_DIRECTION_OUTPUT);
        gpiod_line_settings_set_output_value(led_settings, GPIOD_LINE_VALUE_INACTIVE);

        struct gpiod_line_config *led_cfg = gpiod_line_config_new();
        unsigned int led_offset = offsets[i];
        gpiod_line_config_add_line_settings(led_cfg, &led_offset, 1, led_settings);

        struct gpiod_line_request *led_req = gpiod_chip_request_lines(chip, led_req_cfg, led_cfg);

        gpiod_line_settings_free(led_settings);
        gpiod_line_config_free(led_cfg);

        if (!led_req) {
            fprintf(stderr, "LED line request failed: %s\n", strerror(errno));

            for (int j = 0; j < i; j++) {
                gpiod_line_request_release(out_leds[j].request);
            }
            gpiod_request_config_free(led_req_cfg);
            gpiod_chip_close(chip);
            return -1;
        }
        out_leds[i].request = led_req;
        out_leds[i].offset = led_offset;
    }

    gpiod_request_config_free(led_req_cfg);
    gpiod_chip_close(chip);
    return 0;
}

int btn_config(const char *chip_path, const unsigned int offset, struct gpiod_hw *out_btn) {

    struct gpiod_chip *chip = gpiod_chip_open(CHIP_PATH);
    if (!chip) {
        fprintf(stderr, "gpiod_chip_open failed: %s\n", strerror(errno));
        return -1;
    }

    struct gpiod_line_settings *btn_settings = gpiod_line_settings_new();
    gpiod_line_settings_set_direction(btn_settings, GPIOD_LINE_DIRECTION_INPUT);
    gpiod_line_settings_set_bias(btn_settings, GPIOD_LINE_BIAS_PULL_UP);

    struct gpiod_line_config *btn_cfg = gpiod_line_config_new();
    unsigned int btn_offset = offset;
    gpiod_line_config_add_line_settings(btn_cfg, &btn_offset, 1, btn_settings);

    struct gpiod_request_config *btn_req_cfg = gpiod_request_config_new();
    gpiod_request_config_set_consumer(btn_req_cfg, "oscam-btn");
    
    struct gpiod_line_request *btn_req = gpiod_chip_request_lines(chip, btn_req_cfg, btn_cfg);

    if (!btn_req) {
        fprintf(stderr, "LED line request failed: %s\n", strerror(errno));

        gpiod_line_request_release(out_btn->request);
        gpiod_request_config_free(btn_req_cfg);
        gpiod_chip_close(chip);
        return -1;
    }
        out_btn->request = btn_req;
        out_btn->offset = btn_offset;

    gpiod_request_config_free(btn_req_cfg);
    gpiod_chip_close(chip);
    return 0;
}

int main(void) {

    /* --------- Button & LED ----------- */
    
    signal(SIGINT, handle_sigint);
    int led_offsets = {17, 27, 22};
    int btn_offset = /* */;

    // led output
    struct gpiod_hw *leds;
    memset(&leds, 3, sizeof(*leds));

    if (led_config(CHIP_PATH, &led_offsets, 3, leds) == -1) {
        exit(EXIT_FAILURE);
    }

    // button input
    struct gpiod_hw *btn;
    memset(&btn, 1, sizeof(*btn));

    if (btn_config(CHIP_PATH, btn_offset, btn) == -1) {
        exit(EXIT_FAILURE);
    }
    
    int led_state = 0;
    int last_btn_state = 1;

    /* ------------ Camera ------------- */
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
    while (keep_running) {
        struct v4l2_buffer buf;

        //    ----- Signal handler -----
        enum gpiod_line_value current_btn = gpiod_line_request_get_value(btn_req, BTN_PIN);

        if (current_btn == GPIOD_LINE_VALUE_ACTIVE && last_btn_state == 1) {
            // led_state = !led_state;

            // enum gpiod_line_value new_led_val = led_state ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE;
        

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