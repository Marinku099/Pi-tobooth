CC = gcc
CFLAGS = -Wall -Wextra -g

SRCS = $(wildcard *.c)

OBJS = $(SRCS:.c=.o)

TARGET = oscam

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@
clean:
	rm -f $(OBJS) $(TARGET)