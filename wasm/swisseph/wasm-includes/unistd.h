#ifndef _WASM_SHIM_UNISTD_H
#define _WASM_SHIM_UNISTD_H
#include <stddef.h>
typedef long ssize_t;
ssize_t readlink(const char *path, char *buf, size_t bufsiz);
#endif
