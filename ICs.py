#
#   I C s . p y
#
# This module defines various useful initial conditions (normalized).
#
# STATUS
#   Copied from the corresponding file in 1d_PDEs/Lib. Keep that one
#   until I'm sure about everything.

import numpy as np
import sympy as sy
import scipy.integrate

def n_integrate(integrand, dx):
    return( scipy.integrate.simps(integrand, dx=dx) )

# Normalize a list of REAL points over an interval. The points represent
# our requested intial condition for the wave function. Our IC must be
# real. The initial probability will then be the square of the IC. This
# initial probability must be 1. So, we square the requested IC and then
# normalize.

def normalize_points(x0, xL, points):
    npts = len(points)
    dx = float(xL-x0)/(npts-1)
    squares = []
    for n in range(npts): squares += [ points[n]**2, ]
    nrm = np.sqrt( n_integrate(squares, dx=dx) )
    #print('Dividing by norm fact: %s' %nrm)
    for x in range(npts): points[x] = points[x]/nrm
    return(points)

# I'm making a separate function to normalize complex points.
# After I've gained some confidence with it, perhaps this one function
# will be all I need to normalize points.

def normalize_complex_points(x0, xL, points):
    npts = len(points)
    dx = float(xL-x0)/(npts-1)
    squares = []
    for n in range(npts): squares += [ points[n]*points[n].conjugate(), ]
    nrm = np.sqrt( n_integrate(squares, dx=dx) )
    #print('Dividing by norm fact: %s' %norm)
    for x in range(npts): points[x] = points[x]/nrm
    return(points)

# And here are the actual IC definitions ...

# Constant over the whole defined range
def ic_const(x0, xL, nx):
    ic = []
    for x in range(nx+1): ic += [ 1, ]
    return( normalize_points(x0, xL, ic) )

# Just a '1' -- don't normalize it
def ic_one(x0, xL, nx):
    ic = []
    for x in range(nx+1): ic += [ 1, ]

# Constant, but zero outsize a certain limit
def ic_square(x0, xL, nx, a, b):
    L = float(xL-x0)
    dx = L/nx
    ic = []
    #print('the limits are: %s, %s' %(a,b))
    for xi in range(nx+1):
        x = x0+xi*dx
        if x < a: ic += [ 0, ]
        elif x < b: ic += [ 1, ]
        else: ic += [ 0, ]
    return( normalize_points(x0, xL, ic) )

# Produce a centered Gaussian if center is not specified
def ic_gaussian(x0, xL, nx, center=None, spread=.1):
    if center == None: center = float(xL+x0)/2
    ic = []
    L = float(xL-x0)
    S = spread*L
    dx = L/nx
    for xi in range(nx+1):
        x = x0 + xi*dx
        g = sy.exp(-((x-center)/S)**2)
        ic += [ float(g), ]
    return( normalize_points(x0, xL, ic) )

# Thursday group May 3, 2012 - 
# Initial condition that will move (to the right) instead of just
# spreading out.
def ic_gaussian_right(x0, xL, nx, k0, center=None, spread=.1):
    if center == None: center = float(xL+x0)/2
    ic = []
    L = float(xL-x0)
    S = spread*L
    dx = L/nx
    def mult(x):
        return( sy.exp(-1j*k0*x) )
    for xi in range(nx+1):
        x = x0 + xi*dx
        g = sy.exp(-((x-center)/S)**2)
        m = float(sy.re(mult(x)))  + float(sy.im(mult(x)))*1j
        ic += [ float(g) * m, ]
    return( normalize_complex_points(x0, xL, ic) )

# This creates an initial condition that is the (normalized) sum
# of two sine type eigenfunctions. 
def ic_2sines(x0, xL, nx, c1, c2, n1, n2):
    L = float(xL-x0)
    dx = L/nx
    ic = []
    for xi in range(nx+1):
        x = x0 + xi*dx
        point = float( c1 * sy.sin(n1 * sy.pi * x/L) )
        point += float( c2 * sy.sin(n2 * sy.pi * x/L) )
        ic += [ point, ]
    return( normalize_points(x0, xL, ic) )

