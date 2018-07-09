#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
extern int kk;
extern int kmin;
extern int kmax;
extern int jj;
extern int jmin;
extern int jmax;
extern int ii;
extern int imin;
extern int imax;
extern int i;
extern int jp;
extern int kp;
extern double * __restrict__ b;
extern double * __restrict__ dbl;
extern double * __restrict__ xdbl;
extern double * __restrict__ dbc;
extern double * __restrict__ xdbc;
extern double * __restrict__ dbr;
extern double * __restrict__ xdbr;
extern double * __restrict__ dcl;
extern double * __restrict__ xdcl;
extern double * __restrict__ dcc;
extern double * __restrict__ xdcc;
extern double * __restrict__ dcr;
extern double * __restrict__ xdcr;
extern double * __restrict__ dfl;
extern double * __restrict__ xdfl;
extern double * __restrict__ dfc;
extern double * __restrict__ xdfc;
extern double * __restrict__ dfr;
extern double * __restrict__ xdfr;
extern double * __restrict__ cbl;
extern double * __restrict__ xcbl;
extern double * __restrict__ cbc;
extern double * __restrict__ xcbc;
extern double * __restrict__ cbr;
extern double * __restrict__ xcbr;
extern double * __restrict__ ccl;
extern double * __restrict__ xccl;
extern double * __restrict__ ccc;
extern double * __restrict__ xccc;
extern double * __restrict__ ccr;
extern double * __restrict__ xccr;
extern double * __restrict__ cfl;
extern double * __restrict__ xcfl;
extern double * __restrict__ cfc;
extern double * __restrict__ xcfc;
extern double * __restrict__ cfr;
extern double * __restrict__ xcfr;
extern double * __restrict__ ubl;
extern double * __restrict__ xubl;
extern double * __restrict__ ubc;
extern double * __restrict__ xubc;
extern double * __restrict__ ubr;
extern double * __restrict__ xubr;
extern double * __restrict__ ucl;
extern double * __restrict__ xucl;
extern double * __restrict__ ucc;
extern double * __restrict__ xucc;
extern double * __restrict__ ucr;
extern double * __restrict__ xucr;
extern double * __restrict__ ufl;
extern double * __restrict__ xufl;
extern double * __restrict__ ufc;
extern double * __restrict__ xufc;
extern double * __restrict__ ufr;
extern double * __restrict__ xufr;

void loop()
{
    int __kk_0__ = kk;
    int __jj_1__ = jj;
    int __ii_2__ = ii;

#pragma scop
    for (__kk_0__ = kmin; __kk_0__ <= kmax - 1; __kk_0__ += 1) {
        for (__jj_1__ = jmin; __jj_1__ <= jmax - 1; __jj_1__ += 1) {
            for (__ii_2__ = imin; __ii_2__ <= imax - 1; __ii_2__ += 1) {
                i = __ii_2__ + __jj_1__ * jp + __kk_0__ * kp;
                b[i] = dbl[i] * xdbl[i] + dbc[i] * xdbc[i] + dbr[i] * xdbr[i] + dcl[i] * xdcl[i] + dcc[i] * xdcc[i] + dcr[i] * xdcr[i] + dfl[i] * xdfl[i] + dfc[i] * xdfc[i] + dfr[i] * xdfr[i] + cbl[i] * xcbl[i] + cbc[i] * xcbc[i] + cbr[i] * xcbr[i] + ccl[i] * xccl[i] + ccc[i] * xccc[i] + ccr[i] * xccr[i] + cfl[i] * xcfl[i] + cfc[i] * xcfc[i] + cfr[i] * xcfr[i] + ubl[i] * xubl[i] + ubc[i] * xubc[i] + ubr[i] * xubr[i] + ucl[i] * xucl[i] + ucc[i] * xucc[i] + ucr[i] * xucr[i] + ufl[i] * xufl[i] + ufc[i] * xufc[i] + ufr[i] * xufr[i];
            }
        }
    }

#pragma endscop
    kk = __kk_0__;
    jj = __jj_1__;
    ii = __ii_2__;
}