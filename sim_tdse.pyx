#
# s i m _ t d s e . p y x
#
# TDSE simulation in cython
#
# STATUS
#
#   December 2016: This is basically a clone of the code in my PDEs dir
#

import numpy as np
cimport numpy as cnp
from time import time
from cpython cimport bool

# This is apparently not the correct was to do a 2nd derivative. See:
#   https://ocw.mit.edu/courses/mathematics/ ...
#   18-085-computational-science-and-engineering-i-fall-2008/video-lectures/
#   Lecture 2 around 12 minutes
# But it's doing the job for the time being.
#
cdef second_derivative(
    cnp.ndarray[cnp.float64_t, ndim=1] f, 
    cnp.ndarray[cnp.float64_t, ndim=1] d2,
    int nx, double dx):

    cdef int n
    cdef double over_2dx = 1/(2.0*dx)
    cdef double over_4dx2 = 1/(4.0*dx*dx)

    d1_0 = (f[1] - f[0]) / dx
    d1_1 = (f[2] - f[0]) * over_2dx

    d2[0] = (d1_1 - d1_0) / dx
    d2[1] = (f[3] - f[1]) * over_4dx2 - d1_0 * over_2dx

    for n in range(2, nx-2): d2[n] = (f[n+2] - 2*f[n] + f[n-2]) * over_4dx2

    d1_nx_minus_1 = (f[nx-1] - f[nx-2]) / dx
    d1_nx_minus_2 = (f[nx-1] - f[nx-3]) * over_2dx
    d1_nx_minus_3 = (f[nx-2] - f[nx-4]) * over_2dx

    d2[nx-2] = (d1_nx_minus_1 - d1_nx_minus_3) * over_2dx
    d2[nx-1] = (d1_nx_minus_1 - d1_nx_minus_2) / dx

class sim_tdse:

    def __init__(self,
        npts, dx, psi_0, dt, V, using_bc, ux0=0.0, uxL=0.0):

        self.m = 1.0 # Mass
        self.hbar = 1.0 # Planck's const
        self.using_bc = using_bc
        self.ux0 = np.float64(ux0)
        self.uxL = np.float64(uxL)
        self.npts = int(npts)
        self.dx = np.float64(dx)
        self.dt = np.float64(dt)

        # The first u is psi_0 ...
        # Use numpy arrays for speed
        self.V = np.zeros(npts, dtype=np.float64)   # The potential
        self.u_r = np.zeros(npts, dtype=np.float64) # Real part of psi
        self.u_i = np.zeros(npts, dtype=np.float64) # Imag part of psi
        self.P = np.zeros(npts, dtype=np.float64)   # |psi|^2 (the probability)
        for n in range(npts):
            self.V[n] = V[n]
            self.u_r[n] = psi_0[n].real
            self.u_i[n] = psi_0[n].imag
            self.P[n]=psi_0[n].real*psi_0[n].real+psi_0[n].imag*psi_0[n].imag
        self.t = 0

    def run(self, target_time, break_time):
        real_time = time()

        cdef int x # Used in x loop below
        cdef double m = self.m
        cdef double hbar = self.hbar
        cdef double hBy2m = hbar/(2*m)
        cdef int npts = self.npts
        cdef int nx = self.npts-1 
        cdef double dt = self.dt
        cdef double dx = self.dx
        cdef double ux0 = self.ux0
        cdef double uxL = self.uxL
        cdef int N = 0

        # These make a HUGE difference
        cdef cnp.ndarray[cnp.float64_t, ndim=1] V = self.V
        cdef cnp.ndarray[cnp.float64_t, ndim=1] u_r = self.u_r
        cdef cnp.ndarray[cnp.float64_t, ndim=1] u_i = self.u_i
        cdef cnp.ndarray[cnp.float64_t, ndim=1] P = self.P
        cdef cnp.ndarray[cnp.float64_t, ndim=1] d2u_dx2_r =\
            np.zeros(npts, dtype=np.float64)
        cdef cnp.ndarray[cnp.float64_t, ndim=1] d2u_dx2_i =\
            np.zeros(npts, dtype=np.float64)
        cdef cnp.ndarray[cnp.float64_t, ndim=1] vByh = V/hbar
        cdef cnp.ndarray[cnp.float64_t, ndim=1] du_dt_r =\
            np.zeros(npts, dtype=np.float64)
        cdef cnp.ndarray[cnp.float64_t, ndim=1] du_dt_i =\
            np.zeros(npts, dtype=np.float64)

        while self.t < target_time:
            if time() - real_time > break_time: break

            #
            # Calculate the 2nd derivatives
            #
            second_derivative(u_r, d2u_dx2_r, npts, dx)
            second_derivative(u_i, d2u_dx2_i, npts, dx)

            #
            # Update the probability wave
            #

            # These "Vectorized lines don't work. Don't know why.
            #du_dt_r = -hBy2m * d2u_dx2_i + vByh * u_i
            #du_dt_i =  hBy2m * d2u_dx2_r - vByh * u_r
            #u_r = u_r + du_dt_r*dt
            #u_i = u_i + du_dt_i*dt
            #P = u_r*u_r + u_i*u_i
            
            for x in range(0, npts):
                du_dt_r[x] = -hBy2m * d2u_dx2_i[x] + vByh[x] * u_i[x]
                du_dt_i[x] =  hBy2m * d2u_dx2_r[x] - vByh[x] * u_r[x]
                u_r[x] = u_r[x] + du_dt_r[x]*dt
                u_i[x] = u_i[x] + du_dt_i[x]*dt
                P[x] = u_r[x]*u_r[x] + u_i[x]*u_i[x]

            # Potentially handle Dirichlet (only) boundary conditions here
            if self.using_bc:
                u_r[0] = ux0
                u_i[0] = ux0
                P[0] = u_r[0]*u_r[0] + u_i[0]*u_i[0]
                u_r[nx] = uxL
                u_i[nx] = uxL
                P[nx] = u_r[nx]*u_r[nx] + u_i[nx]*u_i[nx]
            # Update the simulation time
            self.t += dt
            # Count number of iterations
            N += 1

        self.u_r = u_r
        self.u_i = u_i
        self.P = P
        return(N)

