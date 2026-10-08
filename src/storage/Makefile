CC = gcc

fs_main.o fs_manager.o: fs_manager.h

storage: fs_main.o fs_manager.o
	$(CC) -o $@ $^

clean:
	rm -f *.o storage