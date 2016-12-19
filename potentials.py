#---------------------------------------------------------------------------#
#
#   p o t e n t i a l s . p y
#
# This module defines various potentials that are used in some of the
# existing code. The way these are defined right now they are not very
# general, but can at least serve as examples for potentials that you
# might want to define.
#
# STATUS
#   Copied from the corresponding file in 1d_PDEs/Lib. Keep that one
#   until I'm sure about everything.
#
#---------------------------------------------------------------------------#

# make_potential() returns a numpy array (for speed in conjunction with
#   the cython code of the simulator) based on the selected potential
#   function.
#
def make_potential(x_axis, v):
    from numpy import zeros, float32
    V = zeros(len(x_axis), dtype=float32)
    n = 0
    for x in x_axis: 
        V[n] = float(v(x))
        n += 1
    return(V)

# Zero everywhere
def V_Zero(x): return(0.0)

# "Infinite" wells ...

def V_IWell_66(x):
    a=-6; b=6
    V0 = 100
    if x < a: return(V0)
    elif x < b: return(0)
    else: return(V0)

def V_IWell_08(x):
    a=0; b=8
    V0 = 100
    if x < a: return(V0)
    elif x < b: return(0)
    else: return(V0)

# Potential steps ...

def V_Step_Small(x):
    if x < 0: return(0)
    return(0.60)

def V_Step_Large(x): 
    if x < 0: return(0)
    return(1.0)

# Potential barriers ...

def V_Barrier_Large(x):
    if x < 0: return(0)
    elif x > 10: return(0)
    else: return(0.5)

def V_Barrier_Small(x):
    if x < 0: return(0)
    elif x > 10: return(0)
    else: return(.3)

# Linearly varying potentials ...

def V_Linear(x):
    if x < 0: return(0)
    else: return(x*0.05)

def V_Triangle(x):
    mult = .05
    if x < 0: return(0)
    elif x < 10: return(x*mult)
    elif x < 20: return(10*mult - (x-10)*mult)
    else: return(0)

