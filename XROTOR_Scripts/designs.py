import os
import file_tools
import run_prop
import numpy as np
import matplotlib.pyplot as plt
import graphing

# ConstantPower is a object used to calculate, compile and  plot the performance of a fixed pitch
# constant power propeller.

# List of methods:
#   __init__
#   evaluate_aero
#   _get_convergence
#   _aero_eval
#   compile_data
#   plot


class ConstantPower:
    # geom: a PropGeom object containing all the necessary information to evaluate a propeller using XROTOR
    # power: a float describing the amount of power supplied to the propeller
    # vel_aero: a 1D np float array. Each number represents the velocities propeller performance will be evaluated at
    # out_folder: a string containing the root folder that data will be output to
    # eval_structural: a 1D float array. True indicates that you want the propellers structural data evaluated at the
    #                  corresponding vel_aero velocity
    # rpm0: a float estimate of the propeller. Used to estimate the reynolds number airfoil performance is evaluated at
    # altitude: a float containing the altitude that the propeller is at. -1 means underwater

    def __init__(self, geom, power, vel_aero, out_folder, eval_structural=None, fluid=None, rpm0=200):
        self.fluid = fluid
        self.rpm0 = rpm0
        self.geom = geom
        self.vel_list = vel_aero
        self.folder = file_tools.ConstantFolder(out_folder)
        self.power = power
        self.converged_list = np.zeros(len(self.vel_list))
        self.thrust_list = np.zeros(len(self.vel_list))
        self.torque_list = np.zeros(len(self.vel_list))
        self.rpm_list = np.zeros(len(self.vel_list))
        self.efficiency_list = np.zeros(len(self.vel_list))
        self.efficiency_ideal = np.zeros(len(self.vel_list))
        self.advance_ratio = np.zeros(len(self.vel_list))
        self.torque_coef = np.zeros(len(self.vel_list))
        self.thrust_coef = np.zeros(len(self.vel_list))
        self.structural = []
        if eval_structural is None:
            self.eval_structural = np.zeros(len(vel_aero), dtype=bool)
        else:
            self.eval_structural = eval_structural

        if fluid is None:
            self.fluid = {'density': 1000,
                          'viscosity': 10**-6,
                          'speed_sound': 10**5
                          }

    # returns the betz distribution for propeller
    def set_betz(self, pwr, vel, verbose=False):
        run_prop.run_betz(self.geom, vel, self.rpm0, "VRTX", "betz_temp", self.fluid, pwr, verbose)



    # meant to be called after the object is created. Gets aeronautical data by running information through XROTOR.
    def evaluate_aero(self, verbose=False):
        self.folder.reset_data()    # resets the base out_folder if it exists and makes a new one
        file_tools.make_folder(self.folder.aero_folder)  # creates an aerodynamic folder within the out_folder
        if True in self.eval_structural:
            file_tools.make_folder(self.folder.structural_folder)
            self.geom.write_structural(self.folder.structural_geometry)

        for i, vel in enumerate(self.vel_list):
            # runs XROTOR at the velocity
            rpm_guess, solver, converged = self._get_convergence(vel, self.rpm0, verbose)

            # error between the estimated rpm and actual rpm. Corrects so that the reynolds number guess
            # is more accurate
            percent_error = 100*(rpm_guess - self.rpm0) / self.rpm0
            if percent_error > 10:
                rpm_guess, solver, converged = self._get_convergence(vel, rpm_guess, verbose)

            if self.eval_structural[i]:
                # if the data is not aerodynamic data didn't converge don't bother running structural
                if converged:
                    run_prop.evaluate_strength(self.geom, vel, rpm_guess, solver, self.folder.structural_geometry, self.folder.structural_file(vel),
                                               self.fluid, verbose, pwr=self.power)

    # meant to only be called in evaluate_aero. Cycles through solvers to try to ensure convergence.
    # vel: a float containing the velocity to get aerodynamic data at
    # rpm: rpm used to estimate reynolds number for aerodynamic data
    # contents.rpm: the rpm that the propeller spins at according to XROTOR
    # solver: the solver the caused convergence
    # contents.converged: whether XROTOR ever managed to converge
    def _get_convergence(self, vel, rpm, verbose):
        # run is a function created through _aero_eval. Only input needed is the solver
        run = self._aero_eval(vel, rpm, verbose)

        solver = "VRTX"
        run(solver)
        contents = file_tools.ExtractAero(self.folder.vel_file(vel))

        if not contents.converged:
            solver = "POT"
            run(solver)
            contents = file_tools.ExtractAero(self.folder.vel_file(vel))

        if not contents.converged:
            solver = "GRAD"
            run(solver)
            contents = file_tools.ExtractAero(self.folder.vel_file(vel))

        return contents.rpm, solver, contents.converged

    # returns a function that runs the XROTOR at a constant power
    def _aero_eval(self, vel, rpm, verbose):
        def f(solver):
            run_prop.run(self.geom, vel, rpm, solver, self.folder.vel_file(vel), self.fluid, self.power, verbose)
        return f

    # compiles the data in the files output by XROTOR.
    def compile_data(self):
        for i in range(len(self.vel_list)):
            # creates an object that contains all the desired data
            file_contents = file_tools.ExtractAero(self.folder.vel_file(self.vel_list[i]))
            # assigns file_contents data
            self.thrust_list[i] = file_contents.T
            self.torque_list[i] = file_contents.Q
            self.rpm_list[i] = file_contents.rpm
            self.efficiency_list[i] = file_contents.eff
            self.efficiency_ideal[i] = file_contents.eff_ideal
            self.converged_list[i] = file_contents.converged

            if not file_contents.converged:
                self.torque_list[i] = np.NaN
                self.thrust_list[i] = np.NaN
                self.efficiency_list[i] = np.NaN
                self.efficiency_ideal[i] = np.NaN
                self.structural.append(None)
            else:
                if self.eval_structural[i]:
                    self.structural.append(file_tools.ExtractStructural(self.folder.structural_file(self.vel_list[i])))
                    self.structural[i].calc_stress(self.geom.material['elastic_modulus'], self.geom.material['poissons'])
                else:
                    self.structural.append(None)

        self.advance_ratio = advance_ratio_equation(self.vel_list, self.rpm_list, self.geom.diam)
        self.thrust_coef = thrust_coef_equation(self.fluid['density'], self.rpm_list, self.geom.diam, self.thrust_list)
        self.torque_coef = torque_coef_equation(self.fluid['density'], self.rpm_list, self.geom.diam, self.torque_list)

    # creates performance plots
    # name: the name of the plot. ie. "thrust", "torque", "efficiency"
    # save: saves plot
    # disp: displays plot
    def plot_aero(self, name, save=False, disp=False):
        graphing.single_plot(self, name)
        save_aero_plot(save, self.folder, f'{name}.png')
        display_plot(disp)

    def plot_struct(self, name, save=False, disp=False):
        graphing.single_struct_plot(self, name)
        save_struct_plot(save, self.folder, name)
        display_plot(disp)


# Inherits from the ConstantPower class. Evaluates the performance of a constant pitch propeller at various velocities

# edited methods:
# __init__
# evaluate_aero
# _aero_eval

class ConstantRPM(ConstantPower):
    # geom: a PropGeom object containing all the necessary information to evaluate a propeller using XROTOR
    # rpm: the rpm the propeller spins at
    # vel_aero: a 1D np float array. Each number represents the velocities propeller performance will be evaluated at
    # out_folder: a string containing the root folder that data will be output to
    # eval_structural: a 1D float array. True indicates that you want the propellers structural data evaluated at the
    #                  corresponding vel_aero velocity
    # altitude: a float containing the altitude that the propeller is at. -1 means underwater
    def __init__(self, geom, rpm, vel_aero, out_folder, eval_structural=None, fluid=None):
        super().__init__(geom, None, vel_aero, out_folder, eval_structural, fluid=fluid)
        self.rpm_list = rpm * np.ones(len(vel_aero))

    # evaluates the aerodynamic data. Creates output files from XROTOR
    def evaluate_aero(self, verbose=False):
        self.folder.reset_data()    # resets the base out_folder if it exists and makes a new one
        file_tools.make_folder(self.folder.aero_folder)  # creates an aerodynamic folder within the out_folder
        if True in self.eval_structural:
            file_tools.make_folder(self.folder.structural_folder)
            self.geom.write_structural(self.folder.structural_geometry)

        for i, vel in enumerate(self.vel_list):
            _, solver, converged = self._get_convergence(vel, self.rpm_list[0], verbose)
            if self.eval_structural[i]:
                if converged:
                    run_prop.evaluate_strength(self.geom, vel, self.rpm_list[0], solver, self.folder.structural_geometry,
                                               self.folder.structural_file(vel), self.fluid, verbose)

    # returns a function that runs XROTOR at a constant rpm
    def _aero_eval(self, vel, rpm, verbose):
        def func(solver):
            run_prop.run(self.geom, vel, rpm, solver, self.folder.vel_file(vel), self.fluid, verbose=verbose)
        return func


# for a variable pitch constant power propeller design. Inherits from ConstantPower

# edited methods:
# __init__
# evaluate_aero
# compile_data
# find_ideal

class VariablePitch(ConstantPower):
    # geom: a PropGeom object containing all the necessary information to evaluate a propeller using XROTOR
    # power: a float describing the amount of power supplied to the propeller
    # vel_aero: a 1D np float array. Each number represents the velocities propeller performance will be evaluated at
    # offset_list: a 1D float array. The angle offsets that you want evaluated for the propeller
    # out_folder: a string containing the root folder that data will be output to
    # eval_structural: a 1D float array. True indicates that you want the propellers structural data evaluated at the
    #                  corresponding vel_aero velocity
    # rpm0: a float estimate of the propeller. Used to estimate the reynolds number airfoil performance is evaluated at
    # altitude: a float containing the altitude that the propeller is at. -1 means underwater
    def __init__(self, geom, power, vel_aero, offset_list, out_folder, eval_structural=None, fluid=None, rpm0=200):
        super().__init__(geom, power, vel_aero, out_folder, eval_structural, fluid, rpm0)
        self.offset_list = offset_list
        self.vpp_offset = np.zeros(len(vel_aero))
        self.folder = file_tools.VariableFolder(out_folder)
        self.structural = []
        file_tools.make_folder(self.folder.const_folder)

        # creates a ConstantPower object for each angle in offset_list
        self.constant_propellers = []
        for offset in self.offset_list:
            constant_out = os.path.join(self.folder.const_folder, f'{offset:.2f}')
            offset_geometry = geom.create_offset(offset)
            self.constant_propellers.append(ConstantPower(offset_geometry, self.power, self.vel_list, constant_out,
                                                          eval_structural, fluid, rpm0))

    # evaluates the aerodynamic data for each ConstantPower design
    def evaluate_aero(self, verbose=False):
        self.folder.reset_data()
        file_tools.make_folder(self.folder.const_folder)
        for constant_prop in self.constant_propellers:
            constant_prop.evaluate_aero(verbose)

    # compiles all the XROTOR output files
    def compile_data(self):
        for constant_prop in self.constant_propellers:
            constant_prop.compile_data()
        self._find_ideal()

    # compiles data from the ideal angles
    def _find_ideal(self):
        # creates a matrix of the thrust data to find angle with the highest thrust
        thrust_matrix = np.zeros([len(self.offset_list), len(self.vel_list)])
        for i, constant_prop in enumerate(self.constant_propellers):
            thrust_matrix[i, :] = constant_prop.thrust_list
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

            if self.eval_structural[i] is not None:
                self.structural.append(ideal_propeller.structural[i])

    def plot_aero(self, name, save=False, disp=False):
        graphing.vpp_plot(self, name)
        save_aero_plot(save, self.folder, f'{name}.png')
        display_plot(disp)

    def plot_struct(self, name, save=False, disp=False):
        graphing.single_struct_plot(self, name)
        save_struct_plot(save, self.folder, name)
        display_plot(disp)


# equation for the advance coefficient
def advance_ratio_equation(velocity, rpm, diameter):
    return (60 * velocity) / (rpm * diameter)


# equation for the thrust coefficient
def thrust_coef_equation(rho, rpm, diameter, thrust):
    numerator = 60**2 * thrust
    denominator = rho * rpm**2 * diameter**4
    return numerator / denominator


# equation for the torque coefficient
def torque_coef_equation(rho, rpm, diameter, torque):
    numerator = 60**2 * torque
    denominator = rho * rpm**2 * diameter**2
    return numerator / denominator


# will display plot if desired
def display_plot(view):
    if view:
        plt.show()
    else:
        plt.close()


# will save plot if desired
def save_aero_plot(save, folder, name):
    if save:
        file_tools.make_folder(folder.aero_plots)
        plt.savefig(folder.aero_plot_file(name))


def save_struct_plot(save, folder, name):
    if save:
        file_tools.make_folder(folder.structural_plots)
        plt.savefig(folder.struct_plot_file(name))
