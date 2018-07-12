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
#define min(a,b)   ((a) > (b) ? (b) : (a))
#define max(a,b)   ((a) > (b) ? (a) : (b))
#define MAX_THREADS 4
#define lin(s,i,j) ((i)*sz[s]+j)
#define STEP 4

extern int max;

int nthreads;

int rand_a_b(int a, int b){
    return rand()%(b-a) +a;
}
void fill_f(double *V, int n){
    int i; double f,s;
    for(i=0;i<n;i++){f=rand_a_b(1,1000);f=log(1+f/(f+1)); V[i] = f; }
}

void disp(double *V, int n){
    int i;
    for(i=0;i<n;i++){printf("%5.3f ",V[i]);} printf("\n");
}
void fill_diag(double *V, int n){
    int i; double f;
    for(i=0;i<n*n;i++){V[i] = 0; }
    for(i=0;i<n;i++){V[i*n+i] = 0.1; }
}
void fill_c(char *C, int n){
    int i;
    for(i=0;i<n;i++) C[i]=rand_a_b(0,255);
}

long mymalloc(long V){
    void *p;
    posix_memalign(&p,2048,V);
    return (long)p;
}
void zero_f(double *V, int n){int i;for(i=0;i<n;i++)V[i]=0;}

double sum_f(double *V, int n){double f;int i; f=0; for(i=0;i<n;i++) f+=V[i]; return f;}

double now(){
    struct timeval t; double f_t;
    gettimeofday(&t, NULL);
    f_t = t.tv_usec; f_t = f_t/1000000.0; f_t +=t.tv_sec;
    return f_t;
}

double *kron(double *input_v, double *input_u, int *sz, double **A, int N){
    int t, L, R, i, j, k, a, s, b,m;
    double *u,*v,*w;
    u = input_u; v = input_v;
    R = 1;
    L = 1; for(i=0;i<N;i++) L = L*sz[i];
    if(N%2==0) m = N/2; else m = (N+1)/2;
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


void loop()
{
    
    //omp_set_dynamic(0);
    
    int threads = 1;
    double t0, t1,t2,tt;
    int n0;
    int s,i,j,k,N,L,S;
    int *sz;
    double **A, **Av;
    // for(threads=1; threads<=MAX_THREADS;threads++){
    //    omp_set_num_threads(threads);nthreads=threads;
//    srand(0); N = 10; L=1;S=0;
    srand(0); N = max; L=1;S=0;
    sz = malloc(N*sizeof(int));
    A = malloc(N*sizeof(double*));
    Av = malloc(N*sizeof(double*));
    for(s=0;s<N;s++){
        n0 = 4; if(rand_a_b(1,20)%2==0) n0=n0*2; L = L*n0; S+=n0;
        sz[s] = n0;
        A[s] = (double *)mymalloc(n0*n0*sizeof(double));
        fill_f(A[s], n0*n0);
        Av[s] = (double *)mymalloc(STEP*n0*n0*sizeof(double));
        for(i=0;i<n0;i++) for(j=0;j<n0;j++) for(k=0;k<STEP;k++) Av[s][STEP*lin(s,i,j)+k] = A[s][lin(s,i,j)];
    }
    
    double *x  = (double *)mymalloc(L*sizeof(double));
    double *z = (double *)mymalloc(L*sizeof(double));
    double *r;
    fill_f(x, L); zero_f(z, L);

    t1 = now();
    r = kron(z, x, sz, A, N);
    t2 = now(); tt = t2-t1;

}
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
