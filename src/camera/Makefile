CC = gcc
CFLAGS = -Wall -Wextra -g -Ifunc

# Program that has main(). Swap to main_cam.c to build the LED and button (libgpiod) version.
MAIN = main_cam.c
SRCS = $(MAIN) $(wildcard func/*.c)
OBJS = $(SRCS:.c=.o)
LDLIBS = -lgpiod

TARGET = webcam

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDLIBS)

%.o: %.c func/oscam.h
	$(CC) $(CFLAGS) -c $< -o $@

install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)

.PHONY: all install clean
