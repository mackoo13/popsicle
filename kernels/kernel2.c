#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
typedef int I32;
extern I32 Class;
extern char * restrict opnd;
extern const unsigned char* restrict Perl_fold;

void loop()
{
#pragma scop

    for(Class = 0; Class < 256; ++Class)
    {
        if(opnd[1 +(Class >> 3 & 31)] & 1 <<(Class & 7))
        {
            I32 cf = Perl_fold[Class];
            opnd[1 +(cf >> 3 & 31)] |= 1 <<(cf & 7);
        }
    }

#pragma endscop
}
