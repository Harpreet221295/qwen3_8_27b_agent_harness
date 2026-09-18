#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mathlib.h"

int main(int argc, char **argv) {
    int divide = 0;
    int i = 1;
    if (argc > 1 && strcmp(argv[1], "-d") == 0) { divide = 1; i = 2; }
    if (argc - i != 2) { fprintf(stderr, "usage: calc [-d] A B\n"); return 1; }
    double a = atof(argv[i]), b = atof(argv[i + 1]);
    if (divide) {
        double r = divide_nums(a, b);
        printf("%g\n", r);
    } else {
        printf("%g\n", multiply(a, b));
    }
    return 0;
}
