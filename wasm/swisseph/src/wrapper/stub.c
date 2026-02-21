#include <stdio.h>
#include <stdarg.h>

// Variadic function stubs for WASM (can't be implemented in Rust stable)
int fprintf(FILE *stream, const char *format, ...) {
    return 0;
}

int printf(const char *format, ...) {
    return 0;
}

int sprintf(char *str, const char *format, ...) {
    if (str) *str = '\0';
    return 0;
}

int sscanf(const char *str, const char *format, ...) {
    return 0;
}

int snprintf(char *buf, unsigned long n, const char *format, ...) {
    if (buf && n > 0) *buf = '\0';
    return 0;
}
