#include <stdarg.h>

/* Minimal sprintf/snprintf for Swiss Ephemeris in WASM.
 * Handles: %d, %ld, %02d, %8.1f, %s, %c, %%, and zero-padded integers.
 * No heap allocation. Sufficient for SE filename generation and error messages. */

static int write_int(char *buf, int bufrem, int val, int width, char pad) {
    char tmp[20];
    int neg = 0, len = 0, wrote = 0;
    unsigned int uval;
    if (val < 0) { neg = 1; uval = (unsigned int)(-(val + 1)) + 1; } else { uval = (unsigned int)val; }
    if (uval == 0) { tmp[len++] = '0'; }
    else { while (uval > 0) { tmp[len++] = '0' + (uval % 10); uval /= 10; } }
    int total = len + neg;
    /* padding */
    while (total < width && wrote < bufrem) { buf[wrote++] = pad; total++; }
    if (neg && wrote < bufrem) buf[wrote++] = '-';
    for (int i = len - 1; i >= 0 && wrote < bufrem; i--) buf[wrote++] = tmp[i];
    return wrote;
}

static int write_float(char *buf, int bufrem, double val, int width, int prec) {
    char tmp[64];
    int pos = 0;
    if (val < 0) { if (pos < 63) tmp[pos++] = '-'; val = -val; }
    unsigned long ipart = (unsigned long)val;
    double fpart = val - (double)ipart;
    /* integer part */
    char itmp[20]; int ilen = 0;
    if (ipart == 0) { itmp[ilen++] = '0'; }
    else { while (ipart > 0 && ilen < 19) { itmp[ilen++] = '0' + (ipart % 10); ipart /= 10; } }
    for (int i = ilen - 1; i >= 0 && pos < 63; i--) tmp[pos++] = itmp[i];
    if (prec > 0 && pos < 63) {
        tmp[pos++] = '.';
        for (int i = 0; i < prec && pos < 63; i++) {
            fpart *= 10.0;
            int d = (int)fpart;
            tmp[pos++] = '0' + d;
            fpart -= d;
        }
    }
    tmp[pos] = '\0';
    /* width padding */
    int wrote = 0;
    int pad = width - pos;
    while (pad > 0 && wrote < bufrem) { buf[wrote++] = ' '; pad--; }
    for (int i = 0; i < pos && wrote < bufrem; i++) buf[wrote++] = tmp[i];
    return wrote;
}

static int do_vsprintf(char *str, int maxlen, const char *format, va_list ap) {
    int out = 0;
    int lim = maxlen - 1; /* leave room for null */
    const char *f = format;
    while (*f && out < lim) {
        if (*f != '%') { str[out++] = *f++; continue; }
        f++; /* skip '%' */
        if (*f == '%') { str[out++] = '%'; f++; continue; }
        /* parse flags */
        char pad = ' ';
        if (*f == '0') { pad = '0'; f++; }
        /* parse width */
        int width = 0;
        while (*f >= '0' && *f <= '9') { width = width * 10 + (*f - '0'); f++; }
        /* parse precision */
        int prec = -1;
        if (*f == '.') { f++; prec = 0; while (*f >= '0' && *f <= '9') { prec = prec * 10 + (*f - '0'); f++; } }
        /* length modifier */
        int is_long = 0;
        if (*f == 'l') { is_long = 1; f++; }
        /* conversion */
        switch (*f) {
            case 'd': case 'i': {
                int val = is_long ? (int)va_arg(ap, long) : va_arg(ap, int);
                out += write_int(str + out, lim - out, val, width, pad);
                break;
            }
            case 'u': {
                unsigned int val = is_long ? (unsigned int)va_arg(ap, unsigned long) : va_arg(ap, unsigned int);
                out += write_int(str + out, lim - out, (int)val, width, pad);
                break;
            }
            case 'f': {
                double val = va_arg(ap, double);
                if (prec < 0) prec = 6;
                out += write_float(str + out, lim - out, val, width, prec);
                break;
            }
            case 's': {
                const char *s = va_arg(ap, const char *);
                if (!s) s = "(null)";
                while (*s && out < lim) str[out++] = *s++;
                break;
            }
            case 'c': {
                int c = va_arg(ap, int);
                str[out++] = (char)c;
                break;
            }
            default:
                /* Unknown specifier — skip */
                if (*f) { str[out++] = *f; }
                break;
        }
        if (*f) f++;
    }
    str[out] = '\0';
    return out;
}

int fprintf(void *stream, const char *format, ...) {
    (void)stream;
    (void)format;
    return 0;
}

int printf(const char *format, ...) {
    (void)format;
    return 0;
}

int sprintf(char *str, const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    int ret = do_vsprintf(str, 4096, format, ap);
    va_end(ap);
    return ret;
}

int snprintf(char *str, unsigned long n, const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    int ret = do_vsprintf(str, (int)n, format, ap);
    va_end(ap);
    return ret;
}

int sscanf(const char *str, const char *format, ...) {
    (void)str;
    (void)format;
    return 0;
}
