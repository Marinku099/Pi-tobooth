CC = gcc

all: storage

fs_main.o fs_manager.o: fs_manager.h

storage: fs_main.o fs_manager.o
	$(CC) -o $@ $^

install: storage
	install -m 755 storage /usr/local/bin/storage

clean:
	rm -f *.o storage

.PHONY: all clean install
