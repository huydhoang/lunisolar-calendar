#ifndef _WASM_SHIM_DLFCN_H
#define _WASM_SHIM_DLFCN_H
#define RTLD_LAZY 1
#define RTLD_NOW 2
#define RTLD_GLOBAL 3
#define RTLD_LOCAL 4
void *dlopen(const char *filename, int flag);
char *dlerror(void);
void *dlsym(void *handle, const char *symbol);
int dlclose(void *handle);
typedef struct {
    const char *dli_fname;
    void       *dli_fbase;
    const char *dli_sname;
    void       *dli_saddr;
} Dl_info;
int dladdr(const void *addr, Dl_info *info);
#endif
