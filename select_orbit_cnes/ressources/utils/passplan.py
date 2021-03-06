"""
.. passplan.py
    :synopsis: Make a pass plan from list of orbits build by select_orbit
    Created on 17 March 2015
    
.. moduleauthor: Denis BLUMSTEIN
This file is part of the SWOT Hydrology Toolbox
 Copyright (C) 2018 Centre National d’Etudes Spatiales
 This software is released under open source license LGPL v.3 and is distributed WITHOUT ANY WARRANTY, read LICENSE.txt for further details.


"""

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

from datetime import datetime, timedelta
import glob
from math import floor, ceil
from netCDF4 import Dataset
from os.path import basename, join


class Passplan(object):
    """Processing to make pass plan"""

    def __init__(self, IN_orbit_directory, IN_mission_start_time, IN_cycle_duration, IN_simulation_start_time, IN_simulation_stop_time):
        """
        Constructor, initializes the module
        
        :param IN_orbit_directory: full path of directory containing orbit files
        :type IN_orbit_directory: string
        :param IN_mission_start_time: mission start time
        :type IN_mission_start_time: string
        :param IN_cycle_duration: cycle duration (in seconds)
        :type IN_cycle_duration: float
        :param IN_simulation_start_time: simulation start time
        :type IN_simulation_start_time: string
        :param IN_simulation_stop_time: simulation stop time
        :type IN_simulation_stop_time: string
        """
        print("[Passplan] == INIT ==")
        self.orbit_directory = IN_orbit_directory
        self.mission_start_time = IN_mission_start_time
        self.cycle_duration = IN_cycle_duration / 86400.0  # In days
        self.simulation_start_time = IN_simulation_start_time
        self.simulation_stop_time = IN_simulation_stop_time
    
    def run_preprocessing(self):
        """
        Read the orbit files names generated by the module select_orbits"""

        # Various checks of the inputs
        
        try:
            self.simulation_start_time = ascii2date(self.simulation_start_time)
        except ValueError:
            raise ValueError("Invalid Simulation start time")
            
        try:
            self.simulation_stop_time = ascii2date(self.simulation_stop_time)
        except ValueError:
            raise ValueError("Invalid Simulation stop time")
            
        try:
            self.mission_start_time = ascii2date(self.mission_start_time)
        except ValueError:
            raise ValueError("Invalid Mission start time")
            
        if self.simulation_start_time > self.simulation_stop_time:
            raise ValueError("Simulation start time (%s) is AFTER the stop time (%s)" % (self.simulaiton_start_date, self.simulation_stop_date))
            
        if self.mission_start_time > self.simulation_stop_time:
            raise ValueError(
                "Simulation period (%s,%s) is BEFORE the mission start (%s)" %
                (self.simulation_start_date, self.simulation_stop_date, self.mission_start_date))  
            
        # Read the pass time (relative to the beginning of the cycle)
        tpass = []
        tracks = []
        cycles = []
        for filename in glob.glob(self.orbit_directory + '/*.nc'):
            t = pass_time(filename)
            s = basename(filename).split('.')
            s = s[-2].split('_')
            track = int(s[-1])
            cycle = int(s[-3])
            tpass.append(t)
            cycles.append(cycle)
            tracks.append(track)
        self.pass_time = tpass
        self.cycles = cycles
        self.tracks = tracks
    
    def run_processing(self):
        """Compute the pass plan and write it in output file"""
        
        start = self.simulation_start_time - self.mission_start_time
        start = start.days + start.seconds/86400.0
        self.cycle_start = int(floor(start/self.cycle_duration))
        stop = self.simulation_stop_time - self.mission_start_time
        stop = stop.days + stop.seconds/86400.0
        self.cycle_stop = int(ceil(stop/self.cycle_duration))

        # Global pass plan with all the tracks
        f = self.open_pass_plan(-1)
        self.write_pass_plan(f,-1)
        f.close()

        # One pass plan for each available track
        for track in self.tracks:
            f = self.open_pass_plan(track)
            self.write_pass_plan(f,track)
            f.close()

    def open_pass_plan(self,track):
        """Open the pass plan file and write the header """

        if track == -1:    # pass plan with all tracks
            pass_plan = join(self.orbit_directory,"passplan.txt")
        else:            # pass plan for one given track
            pass_plan = join(self.orbit_directory,"passplan_t%04d.txt" % track)
        f = open(pass_plan,"w")
        f.write("# Mission start:    %s\n" % self.mission_start_time.strftime
                                                    ("%Y-%m-%d %H:%M:%S"))
        f.write("# Simulation start: %s\n" % 
                self.simulation_start_time.strftime("%Y-%m-%d %H:%M:%S"))
        f.write("# Simulation stop:  %s\n" % 
                self.simulation_stop_time.strftime("%Y-%m-%d %H:%M:%S"))
        f.write("#\n")
        f.write("#run      cycle orbit MissionTime year DayOfYear       date     time\n")
        return f

    def write_pass_plan(self,f,track):
        """Write the body of the pass plan file"""

        for cycle in range(self.cycle_start,self.cycle_stop+1):
            for k,t in enumerate(self.pass_time):
                if track==-1 or self.tracks[k]==track:
                    t_cycle = timedelta(cycle*self.cycle_duration) + t
                    t_sec = t_cycle.days*86400 + t_cycle.seconds
                    date = self.mission_start_time + t_cycle
                    str_date = date.strftime("%Y-%m-%d %H:%M:%S")
                    if (date >= self.simulation_start_time and
                        date <= self.simulation_stop_time):

                        doy = date - datetime(date.year,1,1)
                        doy = 1. + float(doy.days) + doy.seconds/86400.
                        str_date = date.strftime("%Y-%m-%d %H:%M:%S")
                        f.write('c%3.3d_t%3.3d %6d %4d %11d %4d %9.5f %s\n' % 
                                (cycle, self.tracks[k], cycle,self.tracks[k],
                                t_sec, date.year, doy, str_date))
                        
                        
#############################
                        

def pass_time(filename):
    """Return the relative pass time (wrt to the beginning of the cycle)"""
    ds = Dataset(filename,"r")
    t = timedelta(seconds=float(ds.variables['time'][0]))
    return t


def ascii2date(strdate):
    """Return a datetime object given its ascii representation"""
    try:
        time = datetime.strptime(strdate,"%Y-%m-%d")
    except ValueError as vex:
        print("String %s cannot be converted to date (%s)" % (strdate, vex))
        raise ValueError("Invalid date string")
    return time
