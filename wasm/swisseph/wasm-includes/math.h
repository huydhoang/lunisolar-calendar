#ifndef _WASM_SHIM_MATH_H
#define _WASM_SHIM_MATH_H
#define M_PI 3.14159265358979323846
#define HUGE_VAL 1.0e999
double sin(double x);
double cos(double x);
double tan(double x);
double asin(double x);
double acos(double x);
double atan(double x);
double atan2(double y, double x);
double sqrt(double x);
double log(double x);
double exp(double x);
double pow(double x, double y);
double fabs(double x);
double ceil(double x);
double floor(double x);
double fmod(double x, double y);
double log10(double x);
#endif
