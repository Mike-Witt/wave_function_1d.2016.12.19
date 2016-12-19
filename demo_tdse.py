#---------------------------------------------------------------------------#
#
#   d e m o _ t d s e . p y
#
#---------------------------------------------------------------------------#
#
#   CONTENTS
#
#    1. Quick Start
#    2. Code for the examples given in "Quick Start" (and perhaps others)
#       2.0 run_simulation()
#       2.1 Free Particle
#       2.2 Finite Potential Step
#       2.3 Finite Barrier
#       2.4 Linear Potential
#       2.5 Infinite Well
#
#---------------------------------------------------------------------------#

    #################################################################
    #                                                               #
    #               1. Quick Start                                  #
    #                                                               #
    #################################################################

# To run:
#
#   ipython -i demo_tdse.py
#
# Then do one of these "pre-installed" examples. Just type in the one
# you want. To make it run faster increase "pint" and to make it run
# slower decrease "pint" (unfortunately the value of "pint" is very
# sensitive so sometimes a small increase or decrease will have a
# large effect).
#
#   free_particle() # A free particle with various configuration options
#
#   fstep1()    # Stationary wave encounters a finite potential step
#               # Note how the simulation becomes unstable on the
#               # left hand side, as the wave reaches the left
#               # limit of computation.
#
#   fstep2()    # Moving wave encounters a finite potential step
#   
#   A moving wave encounters a relatively large or small potential barrier
#   barrier_large()
#   barrier_small()
#
#   Linearly varying potentials
#   linear1()   
#   triangle()
#
# Some of these will plot the entire wave function by default, with the
# real part in blue and the imagniary part in red. Some will only plot the
# probability density function. This behaviour can be controlled with the
# "p_only" parameter:
#
#   fstep1(p_only=False) - animates the whole wave function
#   fstep1(p_only=True) - animates only the probability

#---------------------------------------------------------------------------#

    #################################################################
    #                                                               #
    #               2. Examples                                     #
    #                                                               #
    #################################################################

# Whenever this file is loaded, make sure that the cython code for
# them base simulator class and the tdse simulator is all compiled.

import os
print
print('Making sure the cython code is compiled ...')
build_command = 'python build_cython.py build_ext '
build_command += '--inplace > build_cython.out 2>&1'
os.system(build_command)
print('Build output is in: build_cython.out')

#
# Other imports required globally
#

import ICs as IC
import potentials as POT

    #-----------------------------------------------#
    #                                               #
    #           2.0 run_simulation()                #
    #                                               #
    #-----------------------------------------------#

# run_simulation() gives a handy way to:
#
#   (1) Set up the tdse simulator
#   (2) Store the results in a model
#   (3) Play an animation of the retults
#
# Notes:
#
#   - nt is the number of time steps to use for the simulation
#   - nframes is the number of time steps to save in the model
#
# See the various demos below for examples of how to use it.
#
def run_simulation(
    x0, xL, npts, T, nt, nframes, Vfunc, Vscale, ic, delay=.01,
    xlim=None, ylim=(-.75, .75), bc=False, reduce=1, p_only=False):

    from numpy import linspace
    from sim_tdse import sim_tdse
    from model import model_1d
    import potentials as POT

    if xlim == None: xlim = (x0, xL)

    # Set the range and number of points for space and time
    x_axis = linspace(x0, xL, npts)
    t_axis = linspace(0, T, nframes)
    V = POT.make_potential(x_axis, Vfunc)
    # Set the initial condition
    psi_0 = ic

    # Set up the simulation
    sim = sim_tdse(
        psi_0 = psi_0,
        V = V,
        npts = npts,
        dx = float(xL - x0) / (npts-1),
        dt = float(T)/nt,
        using_bc = bc,
        ux0 = 0.0,
        uxL = 0.0)

    # Create a model and use it to run the simulation
    m = model_1d(t_axis, x_axis)
    # Scaled potential function which the model can animate
    def Vs(x,t): return(Vscale*Vfunc(x))
    pot =  m.data_from_function('Potential', Vs)
    pot.color = 'black'

    vars = []
    vars += [ ('Real Psi', sim.u_r), ]
    vars += [ ('Imag Psi', sim.u_i), ]
    vars += [ ('Probability', sim.P), ]
    psi_r, psi_i, P = m.data_from_simulation(sim, vars)
    psi_r.color='blue'
    psi_r.linewidth=.3
    psi_i.color='red'
    psi_i.linewidth=.3

    # Save the model in a default place before playing it
    os.system('mv CURRENT_MODEL.model LAST_MODEL.model')
    m.save('CURRENT_MODEL.model')

    if p_only==False:
        P.color='black'
        P.linewidth=2
        P.linestyle=':'
        m.play([pot, psi_r, psi_i, P],
            reduce=reduce, xlim=xlim, ylim=ylim, 
            delay=delay, window_title='tdse simulation')
    else: 
        P.color='black'
        P.linewidth=1
        P.linestyle='-'
        m.play([pot, P],
            reduce=reduce, xlim=xlim, ylim=ylim, 
            delay=delay, window_title='tdse simulation')

    #-----------------------------------------------#
    #                                               #
    #           2.1 Free Particle                   #
    #                                               #
    #-----------------------------------------------#

# free_particle()
#
# 9 Dec 2013: Appears to be working.
# You can see the difference when you put in bc=True. I oscillates.
# NOTE: "reduce=n" reduces the number of frames that "play" uses
#   to 1 out of n. This provides a way to speed up play() when you
#   have a lot more frames than you really need.
#
# Examples:
#
#  free_particle(ic='stationary')
#  free_particle(ic='moving')
#
def free_particle(p_only=False,
    x0=-10, xL=10, npts=100, T=12, nt=10000, nframes=100,
    bc=False, reduce=1, ic='stationary'):

    if ic == 'stationary': 
        psi_0 = IC.ic_gaussian(x0, xL, npts, center=None, spread=.1)
    elif ic == 'moving':
        psi_0 = IC.ic_gaussian_right(x0, xL, npts, center=-5, k0=-1.0)
    else:
        print('Initial condition type "%s" not recognized.'%ic)
        return

    # If the analytical solution was not requested, then just run
    # the simulation an exit.

    run_simulation(
        x0, xL, npts, T, nt, nframes, Vfunc = POT.V_Zero, p_only=p_only,
        Vscale = 0, ic = psi_0, bc=bc, reduce=reduce)

    #-----------------------------------------------#
    #                                               #
    #           2.2 Finite Potential Step           #
    #                                               #
    #-----------------------------------------------#

# Stationary wave
def fstep1(p_only=True,
    x0=-40, xL=30, npts=500, T=45, nt=100000, nframes=100, bc=False, reduce=1):

    run_simulation(x0, xL, npts, T, nt, nframes,
        Vfunc = POT.V_Step_Small, Vscale = .15, p_only=p_only,
        ic = IC.ic_gaussian(x0, xL, npts, center=-7.5, spread=.05),
        ylim=[-.25, .25], bc=bc, reduce=reduce)

# Right moving wave
def fstep2(p_only=True,
    x0=-70, xL=30, npts=300, T=70, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Step_Large, Vscale = .15,
        ic = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0),
        ylim=[-.25, .25], bc=bc, reduce=reduce)

# Finite Step - Including analytical (transform) solution
#
#   finite_step()
#
# NOTES:
#   - 601 data points is just enough. The sim was still lags "slightly"
#   - Timings for default parms on Vector, 18 Dec 2013:
#       Using Cython:   about 3 minutes
#       Without Cython: about 7 min 50 sec

def finite_step(p_only=True,
    x0=-70, xL=30, npts=601, T=70, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    psi_0 = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0)

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Step_Large, Vscale = .15, ic = psi_0,
        ylim=[-.25, .25], bc=bc, reduce=reduce)

    #-----------------------------------------------#
    #                                               #
    #           2.3 Finite Potential Barrier        #
    #                                               #
    #-----------------------------------------------#

# Right moving wave, large barrier
def barrier_large(p_only=True,
    x0=-70, xL=50, npts=300, T=70, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Barrier_Large, Vscale = .15,
        ic = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0),
        ylim=[-.25, .25], bc=bc, reduce=reduce)
    

# Right moving wave, small barrier
def barrier_small(p_only=True,
    x0=-70, xL=50, npts=300, T=70, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Barrier_Small, Vscale = .15,
        ic = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0),
        ylim=[-.25, .25], bc=bc, reduce=reduce)

    #-----------------------------------------------#
    #                                               #
    #           2.4 Linear Potential                #
    #                                               #
    #-----------------------------------------------#

# For a texbook analysis, see for example:
#   Quantum Mechanics for Scientists and Engineers
#   David A. B. Miller
#   Section 2.11, starting on page 42 (2009 printing)

def linear1(p_only=True,
    x0=-60, xL=50, npts=300, T=100, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Linear, Vscale = .1,
        ic = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0),
        ylim=[-.25, .25], bc=bc, reduce=reduce)

def triangle(p_only=True,
    x0=-60, xL=70, npts=300, T=100, nt=100000, nframes=100, 
    bc=False, reduce=1, ctr=-30):

    run_simulation(x0, xL, npts, T, nt, nframes, p_only=p_only,
        Vfunc = POT.V_Triangle, Vscale = .1,
        ic = IC.ic_gaussian_right(x0, xL, npts, center=ctr, k0=-1.0),
        ylim=[-.20, .20], bc=bc, reduce=reduce)

    #-----------------------------------------------#
    #                                               #
    #           2.5 Infinite Well                   #
    #                                               #
    #-----------------------------------------------#

#
# Simulation only - WORKING IN PDEs / Dec 2013
#
def iwell(p_only=False,
    x0=0, xL=10, npts=200, T=10, nt=1000000, nframes=100, 
    bc=True, reduce=1, N=20, ic_type='const', delay=.2):

    # Choose the initial condition, based on the "ic" string given
    # by the caller.
    if ic_type == 'square': ic = IC.ic_square(x0, xL, npts, 2, 8)
    elif ic_type == 'const': ic = IC.ic_const(x0, xL, npts)
    elif ic_type == 'gaussian': ic = IC.ic_gaussian(x0, xL, npts, spread=.2)
    elif ic_type == 'sines': ic = IC.ic_2sines(x0, xL, npts, 1, 2, 1, 2)
    else:
        raise Exception('Don\'t know how to do initial condition \"%s\"' %ic)

    run_simulation(
        x0, xL, npts, T, nt, nframes, delay=delay,
        Vfunc = POT.V_Zero, Vscale = 0, ic = ic, p_only=p_only,
        ylim=[-.5, .5], bc=bc, reduce=reduce)

#---------------------------------------------------------------------------#

# Print this message at the end of load:
print
print('For help, edit demo_tdse.py and search for: Quick Start')

#---------------------------------------------------------------------------#
