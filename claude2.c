#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h> // for create thread
#include <time.h>
#include <sched.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>
#include <math.h>
#include <x86intrin.h>
#include <errno.h>
#include <papi.h>
#define max(a,b)   ((a) > (b) ? (a) : (b))
#define lin(s,i,j) ((i)*sz[s]+j)
#define STEP 4
#include <time.h>
#include "papi_utils/papi_events.h"
#include "kernels_pb/kernel.h"

void print_result(int set, long_long* values, double time_spent) {
    int event_codes[256];
    int event_count;
    exec(PAPI_list_events(set, event_codes, &event_count));

    for (int i = 0; i < event_count; ++i) {
        printf("%lld,", values[i]);
    }
    printf("%lf\n", time_spent);
}

int main() {

    int set = PAPI_NULL;
    int event_codes[256];
    int event_count;

    initialize();
    exec(PAPI_multiplex_init());

    // I assume the events number and order is deterministic (e.g. we can initialize it each time anew)
    available_event_codes(event_codes, &event_count);
    long_long* values = malloc(event_count * sizeof(long_long));

    exec(PAPI_create_eventset(&set));
    exec(PAPI_assign_eventset_component(set, 0));   // todo get cmp
    exec(PAPI_set_multiplex(set));
    exec(PAPI_add_events(set, event_codes, event_count));

    clock_t begin = clock();

    loop(set, values);

    clock_t end = clock();

    double time_spent = (double)(end - begin) * 1000 / CLOCKS_PER_SEC;
    print_result(set, values, time_spent);
}

//extern int max;
int max = 229999;

int rand_a_b(int a, int b){
    return rand()%(b-a) +a;
}
void fill_f(double *V, int n){
    int i; double f,s;
    for(i=0;i<n;i++){f=rand_a_b(1,1000);f=log(1+f/(f+1)); V[i] = f; }
}

long mymalloc(long V){
    void *p;
    posix_memalign(&p,2048,V);
    return (long)p;
}
void zero_f(double *V, int n){int i;for(i=0;i<n;i++)V[i]=0;}

double now(){
    struct timeval t; double f_t;
    gettimeofday(&t, NULL);
    f_t = t.tv_usec; f_t = f_t/1000000.0; f_t +=t.tv_sec;
    return f_t;
}

double *kron(double *input_v, double *input_u, int *sz, double **A, int N){
    int t, L, R, i, j, k, a, s, b;
    double *u,*v,*w;
    u = input_u; v = input_v;
    R = 1;
    L = 1; for(i=0;i<N;i++) L = L*sz[i];
    for(s = N-1 ; s >= 0 ; s--){
        L = L/sz[s];
        for(a = 0; a < L; a++){ t = a*(sz[s]*R);
            for(j = 0; j < sz[s]; j++)
                for(b = 0; b < R; b++){
                    k = t+j*R+b;
                    v[k] = 0;
                    for(i = 0; i < sz[s]; i++)
                        v[k] += A[s][lin(s,i,j)]*u[(k + (i-j)*R)];
                }
        }
        w = u; u = v; v = w;
        R = R*sz[s];
    }
    if(N%2==0) w=input_u; else w = input_v;
    return w;
}


int loop(int set, long_long* values)
{
    int n0;
    int s,N,L,S;
    int *sz;
    double **A;
    srand(0); N = max; L=1;S=0;
    sz = malloc(N*sizeof(int));
    A = malloc(N*sizeof(double*));

    for(s=0;s<N;s++){
        n0 = 4;
        L = L*n0;
        S+=n0;
        sz[s] = n0;
        A[s] = (double *)mymalloc(n0*n0*sizeof(double));
        fill_f(A[s], n0*n0);
    }

    double *x  = (double *)mymalloc(L*sizeof(double));
    double *z = (double *)mymalloc(L*sizeof(double));
    fill_f(x, L); zero_f(z, L);

    PAPI_start(set);
    kron(z, x, sz, A, N);
    PAPI_stop(set, values);
}
