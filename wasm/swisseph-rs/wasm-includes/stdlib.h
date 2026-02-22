#ifndef _WASM_SHIM_STDLIB_H
#define _WASM_SHIM_STDLIB_H
#include <stddef.h>
void* malloc(size_t size);
void free(void* ptr);
void* realloc(void* ptr, size_t size);
void* calloc(size_t nmemb, size_t size);
double atof(const char* str);
int atoi(const char* str);
long atol(const char* str);
int abs(int j);
long labs(long j);
void exit(int status);
char* getenv(const char* name);
double strtod(const char *nptr, char **endptr);
typedef int (*__compar_fn_t)(const void*, const void*);
void qsort(void* base, size_t nmemb, size_t size, __compar_fn_t compar);
void* bsearch(const void* key, const void* base, size_t nmemb, size_t size, __compar_fn_t compar);
#endif
