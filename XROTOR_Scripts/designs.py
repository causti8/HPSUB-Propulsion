import os
import file_tools
import run_prop
import numpy as np
import matplotlib.pyplot as plt
import graphing
import shutil
import pandas as pd


# this is the generic constant pitch propeller class. It should never be used, it is here to act as a base for the
# ConstantPower, ConstantRPM, and VariablePitch classes.

# methods:
# __init__: initialization is made to be added to in the 3 child classes
# _set_paths: Made to define the folder heigharchy for the ConstantPower and ConstantRPM classes
# vel_file: returns the name an
class ConstantPitchPropeller:
    # geom: a PropGeom object used to describe the geometry of the propeller
    # vel_aero: 1d array containing velocities propeller aerodynamic performance is to be evaluated at
    # vel_structural: a 1d array boolean array indicating whether to evaluate stress at corresponding vel_aero velocity
    # fluid: dictionary containing the properties of the fluid the propeller is in

    def __init__(self, geom, vel, bend, fluid=None, out_folder=None):
        self.fluid = fluid
        self.geom = geom

        self.aero_data = pd.DataFrame(vel, columns=['vel'])
        vel_bend = filter(lambda x: x != 0, vel*bend)
        self.bend_data = pd.DataFrame(vel_bend, columns=['vel'])

        # default fluid to characteristics of water
        if fluid is None:
            self.fluid = {'density': 1000,
                          'kinematic_viscosity': 10**-6,
                          'speed_sound': 10**5
                          }
        else:
            self.fluid = fluid

        # default out_folder name to the name of the PropGeom object
        if out_folder is None:
            self.out_folder = os.path.join('out', geom.name)
        else:
            self.out_folder = out_folder

        self._set_paths()
        make_folder(self.out_folder)

    # defines the folder structure of the design object
    def _set_paths(self):
        self.aero_folder = os.path.join(self.out_folder, 'aero')
        self.aero_plots = os.path.join(self.out_folder, 'aero_plots')
        self.structural_folder = os.path.join(self.out_folder, 'structural')
        self.structural_plots = os.path.join(self.out_folder, 'structural_plots')
        self.speed_file = os.path.join(self.out_folder, 'max_speed.txt')
        self.structural_geometry = os.path.join(self.out_folder, 'structural_geom.txt')

    # returns a velocity file name
    def vel_file(self, vel):
        return os.path.join(self.aero_folder, f'{vel:.2f}.txt')

    # returns a structural file name
    def structural_file(self, vel):
        return os.path.join(self.structural_folder, f'{vel:.2f}.txt')

    def aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def _bend_plot_file(self, name):
        return os.path.join(self.structural_plots, name)

    # meant to be called after the object is created. Evaluates the aerodynamic and structural performance of the
    # propeller design at every velocity in vel_aero. Outputs the performance data as .txt files to the out_folder.
    # verbose: whether to print the XROTOR commands to the console
    def evaluate_performance(self, verbose=False):
        # clearing old files, and creating new folder system
        clear_path(self.out_folder)
        make_folder(self.out_folder)
        make_folder(self.aero_folder)

        if self.bend_data:
            make_folder(self.structural_folder)
            self.geom.write_bend(self.structural_geometry)

        # create the function that evaluates the aerodynamics
        self.run_aero = self._aero_eval(verbose)

        map(self._eval, self.aero_data['vel'])

    # Cycles through solvers to try to ensure convergence.
    # vel: velocity to evaluate aerodynamic data at
    # verbose: whether to print XROTOR commands to console
    def _get_convergence(self, vel):
        # runs using the vortex-element theory
        solver = "VRTX"
        contents = self.run_aero(vel, solver)

        # runs using the potential flow theory
        if not contents.converged:
            solver = "POT"
            contents = self.run_aero(vel, solver)

        # runs using the graded momentum theory
        if not contents.converged:
            solver = "GRAD"
            contents = self.run_aero(vel, solver)
        return contents.rpm, solver, contents.converged

    # function to be defined in child classes
    def _eval(self, verbose):
        pass

    # compiles the data in the files output by XROTOR. Meant to be run after running evaluate_performance
    def compile_data(self):
        self.aero_data['']


        for i, vel in enumerate(self.vel_list):

            file_name = self.vel_file(vel)
            contents = file_tools.ExtractAero(file_name)

            if contents.converged:
                self.thrust_list[i] = contents.thrust
                self.torque_list[i] = contents.torque
                self.rpm_list[i] = contents.rpm
                self.efficiency_list[i] = contents.efficiency
                self.efficiency_ideal[i] = contents.efficiency_ideal
                self.converged_list[i] = contents.converged
                self.power[i] = contents.power

                if self.vel_struct[i]:
                    self.bend_data.append(file_tools.ExtractStructural(self.structural_file(self.vel_list[i])))
                    self.bend_data[i].calc_stress(self.geom.material['elastic_modulus'],
                                                  self.geom.material["poisson's"])
                else:
                    self.bend_data.append(None)

            else:
                self.torque_list[i] = np.NaN
                self.thrust_list[i] = np.NaN
                self.rpm_list[i] = np.NaN
                self.efficiency_list[i] = np.NaN
                self.efficiency_ideal[i] = np.NaN
                self.bend_data.append(None)

        self.advance_ratio = calc_advance_ratio(self.vel_list, self.rpm_list, self.geom.diam)
        self.thrust_coef = calc_thrust_coef(self.fluid['density'], self.rpm_list, self.geom.diam, self.thrust_list)
        self.torque_coef = calc_torque_coef(self.fluid['density'], self.rpm_list, self.geom.diam, self.torque_list)

    # creates performance plots
    # name: the name of the plot. ie. "thrust", "torque", "efficiency"
    # save: saves plot
    # disp: displays plot
    def plot_aero(self, name, save=False, disp=False):
        graphing.single_plot(self, name)
        if save:
            make_folder(self.aero_plots)
            plt.savefig(self.aero_plot_file(name))
        display_plot(disp)

    def plot_struct(self, name, save=False, disp=False):
        graphing.single_struct_plot(self, name)
        if save:
            make_folder(self.structural_plots)
            plt.savefig(self._bend_plot_file(name))
        display_plot(disp)


# ConstantPower is a object used to calculate, compile and  plot the performance of a fixed pitch
# constant power propeller. New inputs for initialization are below
class ConstantPower(ConstantPitchPropeller):
    # power: a float describing the amount of power supplied to the propeller
    # rpm0: estimated propeller rpm used to calculate reynolds number
    def __init__(self, power, geom, vel_aero, vel_bend=None, fluid=None, out_folder=None, rpm0=200):
        super().__init__(geom, vel_aero, vel_bend, fluid, out_folder)
        self.const_power = power
        self.rpm0 = rpm0
        self.rpm_list = np.zeros(len(vel_aero))

    # returns a function that runs the XROTOR aerodynamics at a constant power at a specific velocity
    def _aero_eval(self, verbose):
        def func(vel, solver):
            run_prop.run(self.geom, vel, self.rpm0, solver, self.vel_file(vel), self.fluid, self.const_power, verbose)
            file_name = self.vel_file(vel)
            contents = file_tools.ExtractAero(file_name)
            if contents.converged:
                while abs(contents.rpm - self.rpm0) / contents.rpm > 0.1:
                    self.rpm0 = contents.rpm
                    run_prop.run(self.geom, vel, self.rpm0, solver, self.vel_file(vel), self.fluid, self.const_power,
                                 verbose)
                    contents = file_tools.ExtractAero(file_name)
                self.rpm0 = contents.rpm
            return contents
        return func

    # returns a function that runs XROTOR aerodynamics and structural at a constant power
    def _structural_eval(self, vel, solver, verbose):
        run_prop.evaluate_strength(self.geom, vel, self.rpm0, solver, self.structural_geometry,
                                   self.structural_file(vel), self.fluid, verbose, self.const_power)


# Inherits from the ConstantPower class. Evaluates the performance of a constant pitch propeller at various velocities
class ConstantRPM(ConstantPitchPropeller):
    # rpm: rpm the propeller will spin at
    def __init__(self, rpm, geom, vel_aero, vel_bend=None, fluid=None, out_folder=None):
        super().__init__(geom, vel_aero, vel_bend, fluid, out_folder)
        self.rpm_list = rpm * np.ones(len(vel_aero))

    # returns a function that runs XROTOR at a constant rpm
    def _aero_eval(self, verbose):
        def func(vel, solver):
            run_prop.run(self.geom, vel, self.rpm_list[0], solver, self.vel_file(vel), self.fluid,
                         verbose=verbose)
            contents = file_tools.ExtractAero(self.vel_file(vel))
            return contents
        return func

    def _structural_eval(self, vel, solver, verbose):
        run_prop.evaluate_strength(self.geom, vel, self.rpm_list[0], solver, self.structural_geometry,
                                   self.structural_file(vel), self.fluid, verbose)


# for a variable pitch constant power propeller design. Inherits from ConstantPower
class VariablePitch(ConstantPitchPropeller):
    # geom: a PropGeom object containing all the necessary information to evaluate a propeller using XROTOR
    # power: a float describing the amount of power supplied to the propeller
    # vel_aero: a 1D np float array. Each number represents the velocities propeller performance will be evaluated at
    # offset_list: a 1D float array. The angle offsets that you want evaluated for the propeller
    # out_folder: a string containing the root folder that data will be output to
    # vel_struct: a 1D float array. True indicates that you want the propellers structural data evaluated at the
    #                  corresponding vel_aero velocity
    # rpm0: a float estimate of the propeller. Used to estimate the reynolds number airfoil performance is evaluated at
    # altitude: a float containing the altitude that the propeller is at. -1 means underwater
    def __init__(self, power, geom, vel_aero, offset_list, vel_bend=None, fluid=None, out_folder=None, rpm0=200):
        super().__init__(geom, vel_aero, vel_bend, fluid, out_folder)
        self.const_power = power
        self.offset_list = offset_list
        self.vpp_offset = np.zeros(len(vel_aero))
        self._set_paths()
        self.structural = []

        # creates a ConstantPower object for each angle in offset_list
        self.constant_propellers = []
        for offset in self.offset_list:
            constant_out = os.path.join(self.const_folder, f'{offset:.2f}')
            make_folder(self.const_folder)
            offset_geometry = geom.create_offset(offset)
            self.constant_propellers.append(ConstantPower(self.const_power, offset_geometry, self.vel_list, vel_bend, fluid, constant_out, rpm0))

    def _set_paths(self):
        self.const_folder = os.path.join(self.out_folder, 'constant_pitch')
        self.aero_plots = os.path.join(self.out_folder, 'aero_plots')
        self.structural_plots = os.path.join(self.out_folder, 'structural_plots')
        self.speed_file = os.path.join(self.out_folder, 'max_speed.txt')
        make_folder(self.out_folder)

    # returns the plot file name
    def aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def _bend_plot_file(self, name):
        return os.path.join(self.structural_plots, name)

    # evaluates the aerodynamic data for each ConstantPower design
    def evaluate_performance(self, verbose=False):
        clear_path(self.out_folder)
        make_folder(self.out_folder)
        make_folder(self.const_folder)
        for prop in self.constant_propellers:
            prop.evaluate_performance(verbose)

    # compiles all the XROTOR output files
    def compile_data(self):
        for prop in self.constant_propellers:
            prop.compile_data()
        self._find_ideal()

    # compiles data from the ideal angles
    def _find_ideal(self):
        # creates a matrix of the thrust data to find angle with the highest thrust
        thrust_matrix = np.zeros([len(self.offset_list), len(self.vel_list)])

        for row, prop in enumerate(self.constant_propellers):
            thrust_matrix[row, :] = prop.thrust_list
        # the indices corresponding to the max thrust
        max_indices = np.nanargmax(thrust_matrix, 0)

        for i in range(len(self.vel_list)):
            # picks ConstantPower propeller with the most thrust
            ideal_propeller = self.constant_propellers[max_indices[i]]
            # records the offset angle
            self.vpp_offset[i] = self.offset_list[max_indices[i]]

            # writes all the data
            self.rpm_list[i] = ideal_propeller.rpm_list[i]
            self.thrust_list[i] = ideal_propeller.thrust_list[i]
            self.torque_list[i] = ideal_propeller.torque_list[i]
            self.efficiency_list[i] = ideal_propeller.efficiency_list[i]
            self.advance_ratio[i] = ideal_propeller.advance_ratio[i]
            self.torque_coef[i] = ideal_propeller.torque_coef[i]
            self.thrust_coef[i] = ideal_propeller.thrust_coef[i]

            if self.vel_struct[i] is not None:
                self.structural.append(ideal_propeller.bend_data[i])

    def plot_aero(self, name, save=False, disp=False):
        graphing.vpp_plot(self, name)
        if save:
            make_folder(self.aero_plots)
            plt.savefig(self.aero_plot_file(name))
        display_plot(disp)

    def plot_struct(self, name, save=False, disp=False):
        graphing.single_struct_plot(self, name)
        if save:
            make_folder(self.structural_plots)
            plt.savefig(self._bend_plot_file(name))
        display_plot(disp)


# equation for the advance coefficient
def calc_advance_ratio(velocity, rpm, diameter):
    return (60 * velocity) / (rpm * diameter)


# equation for the thrust coefficient
def calc_thrust_coef(rho, rpm, diameter, thrust):
    numerator = 60**2 * thrust
    denominator = rho * rpm**2 * diameter**4
    return numerator / denominator


# equation for the torque coefficient
def calc_torque_coef(rho, rpm, diameter, torque):
    numerator = 60**2 * torque
    denominator = rho * rpm**2 * diameter**2
    return numerator / denominator


# will display plot if desired
def display_plot(view):
    if view:
        plt.show()
    else:
        plt.close()


def overwrite(file):
    if os.path.isfile(file):
        os.remove(file)


def clear_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def make_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)

