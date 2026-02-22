#ifndef _WASM_SHIM_SYS_STAT_H
#define _WASM_SHIM_SYS_STAT_H
struct stat {
    int st_mode;
    long st_size;
};
int stat(const char *path, struct stat *buf);
#endif
