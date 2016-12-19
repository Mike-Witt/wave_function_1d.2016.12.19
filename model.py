#
# model.py
#
# Notes on save()/load() routines</h3>
#
#  The idea is that I want to be able to create these model from various
#  different sources, including C programs and Mathematica. So I don't want
#  to do things in any "python specific" way, such as pickle.
#
#  But ... maybe I should look at python's "configparser" (or some such)
#
# TTD
# 
# - July 2014: I'm kind of in the middle of adding mp4 animation. It's
#   "sort of" working, but still needs work, passing parameter, etc.
#   The first one I made played with movie player but not with vlc.
#
# - Add some logic to run_stats, like what I have in animate_points()
#   in Mechanics/Liouville/Liouville.py, so that it tracks memory and also
#   prints an estimate of how much longer to go.
#
# - Either the loop or run_stats logic should watch for a keypress and
#   allow the user to interact with the model in progress (at a minimum
#   save what's there and terminate the run).
#

import numpy as np
from time import time, sleep, strftime
import os, sys

MIN = 60.
MINUTE = 60.
HOUR = 60. * MINUTE
DAY = 24. * HOUR

def make_time_string(t):
    # The time is in seconds. Make sure it's a float.
    t = float(t)
    if t > DAY: return( '%.2f days'%(t/DAY) )
    if t > HOUR: return( '%.2f hours'%(t/HOUR) )
    if t > MINUTE: return( '%.2f minutes'%(t/MINUTE) )
    return ( '%.2f seconds'%t )

class run_stats:
    def __init__(self):
        self.update_interval = 2 # Start out every two seconds
        self.start_time = time()
        self.last_update = self.start_time
        self.ucalls_to_update = 0; # Unecessary calls to update()
        self.lcalls_to_update = 0; # Late calls to update()

    def update(self, msg):
        now = time()
        slu = now - self.last_update # Time since last update
        if slu < self.update_interval:
            self.ucalls_to_update +=1
            return(False) # False mean no update
        if slu > self.update_interval + 1:
            self.lcalls_to_update # More than a seconds late 
        self.last_update = now
        str_now = strftime('%Z %Y.%M.%d %X')
        print('%s - %s'%(str_now, msg))
        sst = now-self.start_time # Time since start
        if sst > DAY: self.update_interval=15*MIN
        elif sst > 12*HOUR: self.update_interval=10*MIN
        elif sst > 5*HOUR: self.update_interval=5*MIN
        elif sst > HOUR: self.update_interval=MIN
        elif sst > 10*MIN: self.update_interval=30
        elif sst > MIN: self.update_interval=15
        elif sst > 10: self.update_interval=10
        else: pass
        return(True) # True means did do update

    def final(self, msg):
        now = strftime('%Z %Y.%M.%d %X')
        total_time = make_time_string(time() - self.start_time)
        print('%s - %s'%(now, msg))
        print('    Total run time was: %s'%total_time)
        print('    %s unecessary calls to update'%self.ucalls_to_update)
        print('    %s late calls to update'%self.lcalls_to_update)

class model(object):

    Version = 'None'
   
    def writeln(self, line):
        self.f.write(line)
        self.f.write('\n')

    def readln(self):
        line = self.f.readline()
        line = line.rstrip('\n')
        return(line)

    class variable:
        def __init__(self, model, name=None, value=None, from_file=False):

            if from_file:
                self.load(model)

            else:
                self.name = name
                self.value = value
                self.color = model.colors[model.next_color]
                model.next_color = np.mod(model.next_color+1,len(model.colors))
                self.linestyle='-'
                self.linewidth='1'
                self.plot_type='surface'
                self.alpha=.5 # Default opacity (or transparency)

        def save(self, model):
            model.writeln(self.name)

            # This appear to work whether it's already a numpy array
            # of just a python list:
            model.writeln(str(np.array(self.value).tolist()))

            model.writeln(self.color)
            model.writeln(self.linestyle)
            model.writeln(str(self.linewidth))
            model.writeln(self.plot_type)
            model.writeln(str(self.alpha))

        def load(self, model):
            self.name  = model.readln()
            self.value = eval(model.readln())
            self.color = model.readln()
            self.linestyle = model.readln()
            self.linewidth = eval(model.readln())
            self.plot_type = model.readln()
            self.alpha = eval(model.readln())

    def __init__(self):
        self.vars = [] # Initialize the list of variables
        self.colors = ['blue', 'green', 'red', 'yellow']
        self.next_color = 0

    def list_vars(self):
        for i in range(len(self.vars)):
            print('[%s].name = \'%s\''%(i, self.vars[i].name))

    def make_gif(self,
        temp_dir='temp_dir', gif_delay=False, target_name='animation', D=True):

        if gif_delay==False:
            cnvt_cmnd =\
                'cd ' + temp_dir + '; '\
                + 'convert frame*.png '\
                + target_name + '.gif'
        else:
            cnvt_cmnd =\
                'cd ' + temp_dir + '; '\
                + 'convert ' + '-delay %s frame*.png '%gif_delay\
                + target_name + '.gif'

        if D: print('Convert command:')
        if D: print(cnvt_cmnd)
        os.system(cnvt_cmnd)
        print('Convert command completed')

    # 09 June 2014 - Changes per Vimeo
    #   (1) Upped fps from 5 to 30
    #   (2) Upped bitrate from 3,000 to 5,000 (but vimeo says 5,000k?)
    # IT DOESN'T LOOK ANY BETTER AFTER MAKING THESE CHANGES AND ELIMINATING
    # THE WARNINGS! So I might as well go back to the smaller fps=5, for
    # a much smaller model.
    #
    def make_mp4(self,
        temp_dir='temp_dir', fps=30, target_name='animation', title=None):

        import sys
        start_time = time()
        cnvt_cmnd = 'cd ' + temp_dir + '; '
        cnvt_cmnd += 'avconv '
        cnvt_cmnd += '-y '
        cnvt_cmnd += '-r %s '%fps
        cnvt_cmnd += '-i frame%06d.png '
        cnvt_cmnd += '-r %s '%fps
        cnvt_cmnd += '-b 5000k ' 
        if title!=None:
            cnvt_cmnd += '-metadata title="%s" '%title
        cnvt_cmnd += target_name + '.mp4 '
        cnvt_cmnd += '2>' + temp_dir + '/avconv.out'
        print('Convert command:');
        print(cnvt_cmnd); sys.stdout.flush()
        os.system(cnvt_cmnd)
        cnvt_time = time()-start_time
        print('%s seconds to run the convert command'%cnvt_time)

#
# model_1d
#

class model_1d(model):
    def __init__(self, t_axis=None, x_axis=None, name='model_1d',
        from_file=None):

        if from_file == None:
            super(model_1d, self).__init__()
            self.name = name
            self.t_axis = t_axis
            self.x_axis = x_axis

        else:
            super(model_1d, self).__init__()
            print('Loding from file: %s'%from_file)
            self.load(from_file)

    def save(self, filename):
        self.f = open(filename, 'w')
        self.writeln('class:')
        self.writeln('model_1d')
        self.writeln('Version:')
        self.writeln(self.Version)
        self.writeln('Saved:')
        self.writeln(strftime('%Z %Y.%M.%d %X'))
        self.writeln('name:')
        self.writeln(self.name)
        self.writeln('t_axis:')
        self.writeln(str(np.array(self.t_axis).tolist()))
        self.writeln('x_axis:')
        self.writeln(str(np.array(self.x_axis).tolist()))
        for v in self.vars:
            self.writeln('variable:')
            v.save(self)
            print('Saved variable: %s' % v.name)
        self.writeln('---End---')
        self.f.close()

    def load(self, filename):
        self.f = open(filename, 'r')
        self.readln() # "class:"
        myclass = self.readln() # "model_1d"
        print('Class was: %s' %myclass)
        self.readln() # "Version:"
        version = self.readln() # Version
        print('Version was: %s' %version)
        if version != self.Version:
            print('WARNING:'),
            print('I\'m a version %s model,'%self.Version),
            print('I\'m reading a version %s model'%version)
        self.readln() # "Saved:"
        timeSaved = self.readln() # Time saved
        print('Time Saved: : %s' %timeSaved)
        self.readln() # "name:"
        self.name = self.readln()
        print('Model name: : %s' %self.name)
        self.readln() # "t_axis"
        self.t_axis = eval(self.readln())
        #print('t_axis:')
        #print(self.t_axis)
        self.readln() # "x_axis"
        self.x_axis = eval(self.readln())
        #print('x_axis')
        #print(self.x_axis)
        self.vars = []
        while True:
            foo = self.readln()
            #print('got foo = %s' %foo)
            if foo == 'variable:':
                #print('About to read a variable ...')
                v = self.variable(self, from_file=True)
                self.vars += [ v, ]
                print('Loaded variable: %s' % v.name)
            elif foo == '---End---':
                print('Finished reading file')
                break
            else:
                print('WARNING: Bad ending line ...')
                print(foo)
                break 

    # data_from_matrix() can be used if the data are not from either a
    # function or from one of the "simulators."
    #
    def data_from_matrix(self, name, M):
        # Supply the model with a "variable" in the form of a (3D) matrix
        # where M[t,x] gives the "y" value for a given time and x
        # coordinate.
        # "name" is the name of the variable.

        v = self.variable(self, name, M)
        self.vars += [v,]
        return(v)

    def data_from_function(self, name, f):
        # Variable data from a function.
        # The function must have arguments named "x" and "t"

        print('model_1d: data_from_function()')

        M = [] # Matrix with indices M[t,x]
        end_t = self.t_axis[len(self.t_axis)-1] # Stats report
        stats = run_stats()                     # Stats report
        for t in self.t_axis:
            stats.update('Sim time: %.3f of %.3f'%(t, end_t)) # St. report
            T = []
            for x in self.x_axis: T += [ f(x,t), ]
            M += [ T, ]

        v = self.variable(self, name, M)
        self.vars += [v,]
        return(v)

    # This gets data from one of my "transform" solutions. This is pretty
    # specific to that particular code, as used by "tdse" (circa Dec 2013).
    #
    def data_from_transform(self, name, transform):
        # Variable data from a "function of t."
        # This means a function that takes the time and gives back a list
        # of x points for that time.

        print('model_1d: data_from_transform()')

        RR = []; II = []; PP = [] # Matrices with indices M[t,x]
        end_t = self.t_axis[len(self.t_axis)-1] # Stats report
        stats = run_stats()                     # Stats report
        for t in self.t_axis:
            stats.update('Sim time: %.3f of %.3f'%(t, end_t)) # St. report
            psi_xt = transform(t)
            asol_R = []; asol_I = []; asol_P = []
            for point in range(len(psi_xt)):
                rr = psi_xt[point].real
                ii = psi_xt[point].imag
                asol_R += [ rr, ]
                asol_I += [ ii, ]
                asol_P += [ rr*rr + ii*ii, ]
            RR += [ asol_R, ]
            II += [ asol_I, ]
            PP += [ asol_P, ]

        new_vars = []

        v = self.variable(self, name+'_r', RR)
        self.vars += [v,]
        new_vars += [v,]

        v = self.variable(self, name+'_i', II)
        self.vars += [v,]
        new_vars += [v,]

        v = self.variable(self, name+'_p', PP)
        self.vars += [v,]
        new_vars += [v,]

        return(new_vars)

    # data_from_simulation()
    #   
    #   Runs a simulator, extracting the specified variables from it.
    #   Each variable is specified as (name, pointer), for example:
    #
    #       # Build a model with the real and imaginary parts
    #       # of the wave function.
    #       sim = sim_tdse()
    #       variables = []
    #       variables += [ ('psi_real', sim.u_r), ]
    #       variables += [ ('psi_imag', sim.u_i), ]
    #       psi_r, psi_i = data_from_simulation(sim, variables)
    #
    def data_from_simulation(self, sim, variables):
        import numpy as np

        print('model_1d: data_from_simulation()')

        # Create an array of matrices. Each one will be of the
        # form: M[t,x] for a given variable.
        MA = []
        nvars = len(variables)
        for n in range(nvars): MA += [ [], ]
        end_t = self.t_axis[len(self.t_axis)-1]
        stats = run_stats()
        n = 0
        # 
        # Note that we want to capture the value of all the variables for
        # each time on the t_axis. But when we run the simulator it will
        # actually step based on its own internal number of required time
        # increments. So we need to continue to run it until it actually
        # reaches the time that we need for the model. Every time through
        # the while loop, the simulator will return if it reached the
        # 'update interval' which is in real time (not simulation time).
        # This allows us to report on the progress of the simulation.
        #
        for t in self.t_axis:
            while sim.t < t:
                #print('top of loop, sim.t=%s, t=%s'%(sim.t,t))
                n += sim.run(t, stats.update_interval)
                ustring = 'Sim time: %.3f of %.3f, '%(sim.t, end_t)
                ustring += 'iter=%s, dt=%1.2e'%(n, sim.dt)
                if stats.update(ustring): n = 0

            # Either of these two ways appears to work. It seems like
            # the 2nd way has the advantage that the variable doesn't
            # have to start out as a numpy array?
            #
            #for n in range(nvars): MA[n] += [ variables[n][1].copy(), ]
            for n in range(nvars): MA[n] += [ np.copy(variables[n][1]), ]

        stats.final('Simulation done')
        new_vars = []
        for n in range(nvars):
            v = self.variable(self, variables[n][0], MA[n])
            new_vars += [ v, ]
            self.vars += [ v, ]
        # Caller might need to know just this set of variables?
        return(new_vars)

    # model_1d.play()
    #
    #   Just calls make_frames() with the required arguments.
    #
    def play(self, 
        var_list, xlim=None, ylim=(-1,1), delay=0, D=False, reduce=1,
        step=True, window_title=None):

        self.make_frames(
            var_list, xlim=xlim, ylim=ylim, delay=delay, D=D, play=True,
            reduce=reduce, step=step, window_title=window_title)

    # model_1d.animate()
    #
    #   Calls make_frames(), and then calls either make_gif or make_mp4.
    #   (make_gif and make_mp4 are in the base model class.)
    #
    def animate(self,
        var_list, xlim=None, ylim=None, D=False, window_title=None,
        type='mp4', gif_delay=False, temp_dir='/tmp/mike_make_frames_temp'):

        self.make_frames(var_list, xlim=xlim, ylim=ylim, D=D,
            window_title=window_title, temp_dir=temp_dir)

        if type == 'gif':
            self.make_gif(temp_dir=temp_dir, gif_delay=gif_delay, D=D)
        elif type == 'mp4':
            self.make_mp4(temp_dir=temp_dir, title=None)
        else:
            print('Unrecognized animation type: \'%s\''%type)

    # model_1d.make_frames()
    #
    #   if play==True, we're doing a play() command, displaying the
    #   sequence of frames to the user.
    #
    #   if play==False, we're storing the frames in a temporary
    #   directory. Presumably so that they can be animated.
    #
    #   D is for debug.
    #
    def make_frames(self,
        var_list, xlim=None, ylim=None, delay=0, D=True,
        step=True, window_title=None, play=False, reduce=1,
        temp_dir='/tmp/mike_make_frames_temp'):

        import numpy as np
        from time import sleep
        import pylab

        if D: print('model_1d: make_frames(): Debugging on')

        if play==False:
            # The temp directory will be erased when we start. But we'll
            # leave it there when we're done
            os.system('rm -rf %s'%temp_dir)
            os.system('mkdir %s'%temp_dir)
            step = False
            delay = 0

        if window_title==None: window_title = self.name

        # Handle a single var that's not on a list
        if np.shape(var_list) == (): var_list = [var_list]

        # Setup plot

        if play==True: pylab.ion()
        else: pylab.ioff()

        fig = pylab.figure()
        ax = fig.gca()
        vars = [] # "Handles" of plotted variables
        # Let user see the initial state and adjust the window.
        fig.canvas.set_window_title(window_title)
        # Keep track of maximum and minimum values
        maxs = []; mins = []
        for v in var_list:
            maxs += [ np.amax(v.value), ]
            mins += [ np.amin(v.value), ]
            plot_data = v.value[0]
            if D: print('Initial value of variable %s' %v.name)
            if D: print('plot color is: %s'%v.color)
            foo, = ax.plot(self.x_axis, plot_data, label=v.name, color=v.color,
                linestyle=v.linestyle, linewidth=v.linewidth, alpha=v.alpha)
            vars += [foo,]
            pylab.legend(loc='lower right', prop={'size':12})

        if xlim == None:
            # Set the limits to match the x axis
            ax.set_xlim([self.x_axis[0], self.x_axis[-1]])
        else: ax.set_xlim(xlim)
        if ylim == None: 
            # Use the max/min data values in any of the variables
            ax.set_ylim([min(mins), max(maxs)])
        else: ax.set_ylim(ylim)

        frame_number = 0
        if play==False:
            pylab.savefig(
                    temp_dir+'/frame%s.png'%str(frame_number).rjust(6,'0'))

        for ti in range(len(self.t_axis)):

            frame_number += 1

            # This provides a way to only do every n frames. I'm calling the
            # variable "reduce" (rather than "n"). I'll want to follow this up
            # by having a model.reduce(n) method that actually prunes all the
            # models variables to save only 1 out of n time values.
            if np.mod(frame_number, reduce) != 0: continue

            t = self.t_axis[ti]
            if D: print('Frame %s'%frame_number)
            for i in range(len(var_list)):
                if D:
                    print('  Plotting ...')
                    print('  variable %s, t = %.2f'%(var_list[i].name, t))
                    sleep(3)
                    print('  value %s, t = %.2f'%(var_list[i].value, t))
                    sleep(3)
                vars[i].set_ydata(var_list[i].value[ti])
            ax.set_ylim(ylim)
            if xlim != None: ax.set_xlim(xlim)
            pylab.title('t = %.3f'%t)

            if play==True:
                pylab.draw()
                pylab.show()
                # This appears to be new. Need to use "pause" instead of sleep.
                # Or it may be because of the specific backend. Some need it?
                if delay != 0: pylab.pause(delay)
                if step:
                    c = raw_input('s)tep, r)un, or q)uit: ')
                    if c=='q': return
                    if c=='r': step = False

            if play==False:
                pylab.savefig(
                    temp_dir+'/frame%s.png'%str(frame_number).rjust(6,'0'))

#
# model_2d
#

class model_2d(model):
    def __init__(self, t_axis=None, x_axis=None, y_axis=None, name='model_2d',
        from_file=None):

        if from_file==None:
            super(model_2d, self).__init__()
            self.name = name
            self.t_axis = t_axis
            self.x_axis = x_axis
            self.y_axis = y_axis
        else:
            super(model_2d, self).__init__()
            print('Loding from file: %s'%from_file)
            self.load(from_file)

    def save(self, filename):
        self.f = open(filename, 'w')
        self.writeln('class:')
        self.writeln('model_2d')
        self.writeln('Version:')
        self.writeln(self.Version)
        self.writeln('Saved:')
        self.writeln(strftime('%Z %Y.%M.%d %X'))
        self.writeln('name:')
        self.writeln(self.name)
        self.writeln('t_axis:')
        self.writeln(str(np.array(self.t_axis).tolist()))
        self.writeln('x_axis:')
        self.writeln(str(np.array(self.x_axis).tolist()))
        self.writeln('y_axis:')
        self.writeln(str(np.array(self.y_axis).tolist()))
        for v in self.vars:
            self.writeln('variable:')
            v.save(self)
            print('Saved variable: %s' % v.name)
        self.writeln('---End---')
        self.f.close()

    def load(self, filename):
        self.f = open(filename, 'r')
        self.readln() # "class:"
        myclass = self.readln() # "model_2d"
        print('Class was: %s' %myclass)
        self.readln() # "Version:"
        version = self.readln() # Version
        print('Version was: %s' %version)
        if version != self.Version:
            print('WARNING:'),
            print('I\'m a version %s model,'%self.Version),
            print('I\'m reading a version %s model'%version)
        self.readln() # "Saved:"
        timeSaved = self.readln() # Time saved
        print('Time Saved: : %s' %timeSaved)
        self.readln() # "name:"
        self.name = self.readln()
        print('Model name: : %s' %self.name)

        self.readln() # "t_axis"
        self.t_axis = eval(self.readln())
        print('t_axis:')
        print(self.t_axis)

        self.readln() # "x_axis"
        self.x_axis = eval(self.readln())
        print('x_axis')
        print(self.x_axis)

        self.readln() # "y_axis"
        self.y_axis = eval(self.readln())
        print('y_axis')
        print(self.y_axis)

        self.vars = []
        while True:
            foo = self.readln()
            print('got foo = %s' %foo)
            if foo == 'variable:':
                print('About to read a variable ...')
                v = self.variable(self, from_file=True)
                self.vars += [ v, ]
                print('Loaded variable: %s' % v.name)
            elif foo == '---End---':
                print('Finished reading file')
                break
            else:
                print('WARNING: Bad ending line ...')
                print(foo)
                break 

    def data_from_matrix(self, name, M):
        # Supply the model with a "variable" in the form of a (4D) matrix
        # where M[t,x,y] gives the "z" value for a given time and xy
        # coordinates.
        # "name" is the name of the variable.

        v = self.variable(self, name, M)
        self.vars += [v,]
        return(v) # Return index to new variable

    def data_from_function(self, name, f):
        # Variable data from a function.
        # The function must have arguments named "x", "y", and "t"

        print('model_2d: data_from_function()')

        M = [] # Matrix with indices M[t,x,y]
        end_t = self.t_axis[len(self.t_axis)-1] # Stats report
        stats = run_stats()                     # Stats report
        for t in self.t_axis:
            stats.update('Sim time: %.3f of %.3f'%(t, end_t)) # St. report
            T = []
            for x in self.x_axis:
                X = []
                for y in self.y_axis:
                    X += [ f(x=x,y=y,t=t), ]
                T += [ X, ]
            M += [ T, ]

        v = self.variable(self, name, M)
        self.vars += [v,]
        return(v) # Return index to new variable

    # Note: D is for Debug
    def play(self, 
        var_list, zlim=(-1,1), delay=0, D=False, step=True, window_title=None):

        import numpy as np
        from time import sleep
        import pylab
        from mpl_toolkits.mplot3d import Axes3D

        if window_title==None: window_title=self.name

        # Handle a single var that's not on a list
        if np.shape(var_list) == (): var_list = [var_list]

        # Setup for plotting
        X,Y=np.meshgrid(self.x_axis, self.y_axis)
        pylab.ion()
        fig = pylab.figure()
        ax = fig.gca(projection='3d')
        
        # All variables must have common indices: t, x, and y
        # NOTE: I imagine that "stuff" will have to be an array
        # in order to handle more than one variable???
        first_time = True
        stuff = []
        for ti in range(len(self.t_axis)):
            t = self.t_axis[ti]

            # Don't want to do these things the very first time
            if first_time == False:
                sleep(delay)
                for s in stuff: s.remove()
                stuff = []
            first_time = False

            for v in var_list:
                if D: print('Plotting variable %s at time %s'%(v.name, t))
                plot_data = v.value[ti]
                if v.plot_type=='surface':
                    thePlot = ax.plot_surface(
                        X, Y, plot_data, rstride=1, cstride=1, linewidth=0,
                        color=v.color, alpha=v.alpha)
                elif v.plot_type=='wireframe':
                    thePlot = ax.plot_wireframe(
                        X, Y, plot_data, rstride=1, cstride=1, 
                        linewidth=v.linewidth,
                        color=v.color, alpha=v.alpha)
                else:
                    e = 'model variable: %s, '%v.name
                    e += 'type "%s" not recognized. '
                    e += 'Should have been "surface" or "wireframe"'
                    raise Exception(e)

                stuff += [ thePlot, ]
            ax.set_zlim(zlim)
            #pylab.title('t = %.3f'%t) # This appears to move with data?
            fig.canvas.set_window_title('%s, t = %.03f'%(window_title,t))
            pylab.draw()
            pylab.show()

