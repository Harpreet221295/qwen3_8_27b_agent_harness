CC = gcc
CFLAGS = -Wall -Werror

calc: main.o mathlib.o
    $(CC) $(CFLAGS) -o calc main.o

main.o: main.c
	$(CC) $(CFLAGS) -c main.c

clean:
	rm -f *.o
