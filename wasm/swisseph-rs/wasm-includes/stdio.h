#ifndef _WASM_SHIM_STDIO_H
#define _WASM_SHIM_STDIO_H
#include <stddef.h>
#include <stdarg.h>
typedef long long off_t;
typedef struct FILE FILE;
extern FILE* const stdin;
extern FILE* const stdout;
extern FILE* const stderr;
FILE* fopen(const char* filename, const char* mode);
int fclose(FILE* stream);
size_t fread(void* ptr, size_t size, size_t nmemb, FILE* stream);
size_t fwrite(const void* ptr, size_t size, size_t nmemb, FILE* stream);
int fseek(FILE* stream, long offset, int whence);
long ftell(FILE* stream);
int fprintf(FILE* stream, const char* format, ...);
int sprintf(char* str, const char* format, ...);
int snprintf(char* str, size_t n, const char* format, ...);
int printf(const char* format, ...);
int sscanf(const char* str, const char* format, ...);
char* fgets(char* str, int n, FILE* stream);
int fflush(FILE* stream);
int fseeko(FILE* stream, off_t offset, int whence);
off_t ftello(FILE* stream);
void rewind(FILE* stream);
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2
#define EOF (-1)
#endif
