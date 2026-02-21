/*
 * C stub providing variadic-function shims for wasm32-unknown-unknown.
 * Rust stable cannot define C-variadic functions, so we provide trivial
 * implementations here (called by the Swiss Ephemeris C code for error
 * messages and string formatting — none of which matter for benchmarking).
 */

#include <stdarg.h>

int sprintf(char *buf, const char *fmt, ...) {
    if (buf) *buf = '\0';
    return 0;
}

int snprintf(char *buf, unsigned long n, const char *fmt, ...) {
    if (buf && n > 0) *buf = '\0';
    return 0;
}

int fprintf(void *stream, const char *fmt, ...) {
    return 0;
}

int printf(const char *fmt, ...) {
    return 0;
}

int sscanf(const char *str, const char *fmt, ...) {
    return 0;
}
