#include "oscam.h"
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <gpiod.h>
#include <signal.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define CHIP_PATH "/dev/gpiochip4" // NOTE: MUST recheck with real environment
#define N_LEDS 3

typedef enum {
    GPIO_TYPE_LED,
    GPIO_TYPE_BUTTON
} gpio_type_t;

volatile sig_atomic_t keep_running = 1;

struct gpio_hw {
    struct gpiod_line_request *request;
    unsigned int offset;
    gpio_type_t type;
};

// ---------- inner functions for HW ----------

void handle_sigint(int sig) {
    signal(sig, SIG_IGN);
    keep_running = 0;
}

int led_config(const char *chip_path, const unsigned int offset, struct gpio_hw *out_led) {

    // open gpio chip 
    struct gpiod_chip *chip = gpiod_chip_open(CHIP_PATH);
    if (!chip) {
        fprintf(stderr, "gpiod_chip_open failed: %s\n", strerror(errno));
        return -1;
    }

    // led output
    struct gpiod_request_config *led_req_cfg = gpiod_request_config_new();
    gpiod_request_config_set_consumer(led_req_cfg, "oscam-led");

    struct gpiod_line_settings *led_settings = gpiod_line_settings_new();
    gpiod_line_settings_set_direction(led_settings, GPIOD_LINE_DIRECTION_OUTPUT);
    gpiod_line_settings_set_output_value(led_settings, GPIOD_LINE_VALUE_INACTIVE);

    struct gpiod_line_config *led_cfg = gpiod_line_config_new();
    unsigned int led_offset = offset;
    gpiod_line_config_add_line_settings(led_cfg, &led_offset, 1, led_settings);

    struct gpiod_line_request *led_req = gpiod_chip_request_lines(chip, led_req_cfg, led_cfg);

    gpiod_line_settings_free(led_settings);
    gpiod_line_config_free(led_cfg);

    if (!led_req) {
        fprintf(stderr, "LED line request failed: %s\n", strerror(errno));
        gpiod_line_request_release(out_led->request);
        gpiod_request_config_free(led_req_cfg);
        gpiod_chip_close(chip);
        return -1;
    }
    out_led->request = led_req;
    out_led->offset = led_offset;
    out_led->type = GPIO_TYPE_LED;

    gpiod_request_config_free(led_req_cfg);
    gpiod_chip_close(chip);
    return 0;
}

int btn_config(const char *chip_path, const unsigned int offset, struct gpio_hw *out_btn) {

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
    out_btn->type = GPIO_TYPE_BUTTON;

    gpiod_request_config_free(btn_req_cfg);
    gpiod_chip_close(chip);
    return 0;
}

int button_is_pressed(struct gpiod_line_request *req, unsigned int offset) {
    return gpiod_line_request_get_value(req, offset) == GPIOD_LINE_VALUE_ACTIVE;
}

void led_set(struct gpio_hw *led, int on) {

    if (led->type != GPIO_TYPE_LED) return;   
    
    gpiod_line_request_set_value(led->request, led->offset, on ? GPIOD_LINE_VALUE_ACTIVE : GPIOD_LINE_VALUE_INACTIVE);
}

void open_all_led(struct gpio_hw *led, int n_leds) {
    if (led->type != GPIO_TYPE_LED) return;
    
    for (int i = 0; i < n_leds; i++) {
        led_set(&led[i], 1);
    }
}

void close_all_led(struct gpio_hw *led, int n_leds) {
    if (led->type != GPIO_TYPE_LED) return;

    for (int i = 0; i < n_leds; i++) {
        led_set(&led[i], 0);
    }
}

void countdown_led(struct gpio_hw *leds, int n_leds, int deley_time){
    close_all_led(leds, n_leds);

    for (int i = 0; i < n_leds; i++) {
        sleep(deley_time);
        led_set(&leds[i], 1);
    }
    sleep(deley_time);
    close_all_led(leds, n_leds);
}

int main(void) {

    /* --------- Button & LED ----------- */
    
    signal(SIGINT, handle_sigint);
    // Define PIN for leds and button
    const int led_offsets[N_LEDS] = {17, 27, 22};
    const int btn_offset = 23;

    // led output
    struct gpio_hw *leds;
    memset(&leds, N_LEDS, sizeof(*leds));

    for (int i = 0; i < N_LEDS; i++) {
        if (led_config(CHIP_PATH, led_offsets[i], &leds[i]) == -1) {
            for (int j = 0; j < i; j++) gpiod_line_request_release(leds[j].request);
            exit(EXIT_FAILURE);
        }
    }

    // button input
    struct gpio_hw *btn;
    memset(&btn, 1, sizeof(*btn));

    if (btn_config(CHIP_PATH, btn_offset, btn) == -1) {
        exit(EXIT_FAILURE);
    }

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
        //    ----- Signal handler -----
        if (button_is_pressed(btn->request, btn_offset)) {
            while (keep_running && button_is_pressed(btn->request, btn_offset)) {
                usleep(10000);
            } 

            countdown_led(leds, N_LEDS, 1);
            // If button pressed -> shoot 4 frames (hope for at least 1 success frame)
            // NOTE: Every frame still in buffers
            bool success_shoot_flag = false;
            struct v4l2_buffer buf;
            for (int frame = 0; frame < n_frames; frame++) {
                if (oscam_capture(fd, buffers, &buf) == -1) {
                    continue;
                }
                success_shoot_flag = true;
                break;   
            }

            if (success_shoot_flag) {
                open_all_led(leds, N_LEDS);
                sleep(1);
                close_all_led(leds, N_LEDS);
            } else {
                fprintf(stderr, "Main: failed to capture after %d attempts\n", n_frames);
                close_all_led(leds, N_LEDS);
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