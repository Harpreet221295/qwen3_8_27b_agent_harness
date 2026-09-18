#!/usr/bin/env bash
cd /app
cat > Makefile <<'MK'
CC = gcc
CFLAGS = -Wall -Werror

calc: main.o mathlib.o
	$(CC) $(CFLAGS) -o calc main.o mathlib.o

main.o: main.c mathlib.h
	$(CC) $(CFLAGS) -c main.c

mathlib.o: mathlib.c mathlib.h
	$(CC) $(CFLAGS) -c mathlib.c

clean:
	rm -f *.o calc
MK
cat > mathlib.c <<'C'
#include <stdio.h>
#include <stdlib.h>
#include "mathlib.h"

double multiply(double a, double b) { return a * b; }

double divide_nums(double a, double b) {
    if (b == 0) { fprintf(stderr, "error: division by zero\n"); exit(2); }
    return a / b;
}
C
