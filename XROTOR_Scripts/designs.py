import os
import file_tools
import run_prop
import numpy as np
import matplotlib.pyplot as plt
import graphing
import pandas as pd
import scipy.integrate as integrate
import shutil


class ConstantPitchPropeller:
    def __init__(self, geom, vel, bend=True, fluid=None, out_folder=None):
        self.verbose = False
        self.geom = geom
        self.bend = bend
        self.aero_data = pd.DataFrame(data=np.round(vel, 3), columns=['vel'])
        self.bend_data = None
        self.race_data = pd.DataFrame()

        # default fluid to characteristics of water
        if fluid is None:
            self.fluid = {'density': 1000,
                          'kinematic_viscosity': 10**-6,
                          'speed_sound': 10**5
                          }
        else:
            self.fluid = fluid

        if out_folder is None:
            self.out_folder = os.path.join('out', geom.name)
        else:
            self.out_folder = out_folder
        make_folder(self.out_folder)

        self.aero_folder = os.path.join(self.out_folder, 'aero')
        self.aero_plots = os.path.join(self.out_folder, 'aero_plots')
        self.bend_folder = os.path.join(self.out_folder, 'bend')
        self.structural_plots = os.path.join(self.out_folder, 'structural_plots')
        self.speed_file = os.path.join(self.out_folder, 'max_speed.txt')
        self.bend_geom = os.path.join(self.out_folder, 'bend_geom.txt')

    # returns a velocity file name
    def _aero_file(self, vel):
        return os.path.join(self.aero_folder, f'{vel:.2f}.txt')

    # returns a structural file name
    def _bend_file(self, vel):
        return os.path.join(self.bend_folder, f'{vel:.2f}.txt')

    def _aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def _bend_plot_file(self, name):
        return os.path.join(self.structural_plots, name)

    def eval_performance(self, verbose=False):
        self.verbose = verbose
        # clearing old files, and creating new folder system
        clear_path(self.out_folder)
        make_folder(self.out_folder)
        make_folder(self.aero_folder)

        if self.bend:
            make_folder(self.bend_folder)
            self.geom.write_bend(self.bend_geom)
        [self.eval_vel(vel) for vel in self.aero_data['vel']]

    # function to run at each velocity
    def eval_vel(self, verbose):
        pass

    # evaluate aerodynamic performance at constant power
    def _run_vel(self, vel, rpm, solver, pwr=None):
        aero_file = self._aero_file(vel)
        if self.bend:
            bend_file = self._bend_file(vel)
        else:
            bend_file = None
        run_prop.run(self.geom, vel, rpm, solver, aero_file, self.fluid,
                     pwr, self.bend_geom, bend_file, verbose=self.verbose)

    def compile_data(self):
        aero_data = []
        for vel in self.aero_data['vel']:
            file_name = self._aero_file(vel)
            aero_data.append(file_tools.extract_aero(file_name))
        self.aero_data = self.aero_data.join(pd.DataFrame(aero_data))

        bend_data = []
        if self.bend:
            for vel in self.aero_data['vel']:
                file_name = self._bend_file(vel)
                df = file_tools.extract_bend(file_name, self.geom.material)
                df['vel'] = [vel for _ in range(len(df))]
                bend_data.append(df)
            self.bend_data = pd.concat(bend_data, axis=0, ignore_index=True)

    def calc_speed(self, sub):
        num_refined = 500
        self.race_data['vel'] = np.linspace(min(self.aero_data['vel']), max(self.aero_data['vel']), num_refined)
        thrust_refined = np.interp(self.race_data['vel'], self.aero_data['vel'], self.aero_data['thrust'])

        numerator = sub['mass'] * self.race_data['vel']

        drag = self.fluid['density'] * sub['frontal_area'] * self.race_data['vel'] ** 2 * sub['drag_coef']
        denominator = thrust_refined - drag
        integrand = numerator / denominator
        negative_indices = integrand < 0
        integrand[negative_indices] = np.NaN

        self.race_data['displacement'] = np.zeros(len(self.race_data))
        self.race_data['displacement'][0] = 0
        self.race_data['displacement'][1:] = integrate.cumtrapz(integrand, self.race_data['vel'])

    def plot_aero(self, *names, save=False, disp=False):
        for name in names:
            graphing.single_plot(name, self.aero_data)
            if save:
                make_folder(self.aero_plots)
                plt.savefig(self._aero_plot_file(name))
            display_plot(disp)

    def plot_struct(self, *names, save=False, disp=False):
        for name in names:
            graphing.single_struct_plot(name, self.bend_data)
            if save:
                make_folder(self.structural_plots)
                plt.savefig(self._bend_plot_file(name))
            display_plot(disp)

    def plot_race(self, initial_gate, final_gate, save=False, disp=False):
        graphing.plot_race(self.race_data, initial_gate, final_gate)
        if save:
            plt.savefig(os.path.join(self.out_folder, 'race.png'))
        display_plot(disp)


class ConstantPower(ConstantPitchPropeller):
    def __init__(self, power, geom, vel, bend=False, fluid=None, out_folder=None, rpm0=200):
        out_folder = os.path.join('out', f'{geom.name}_pwr') if out_folder is None else out_folder
        super().__init__(geom, vel, bend, fluid, out_folder)
        self.const_power = power
        self.rpm0 = rpm0

    def eval_vel(self, vel):
        solvers = ['GRAD', 'POT', 'VRTX']
        solv = solvers.pop()
        self._run_vel(vel, self.rpm0, solv, self.const_power)
        contents = file_tools.extract_aero(self._aero_file(vel))
        rpm_err = abs(self.rpm0 - contents['rpm']) / contents['rpm']
        while rpm_err > 0.1 or not contents['converged']:
            if not contents['converged']:
                if solvers:
                    solv = solvers.pop()
                else:
                    break
            self.rpm0 = contents['rpm']
            self._run_vel(vel, self.rpm0, solv, self.const_power)
            contents = file_tools.extract_aero(self._aero_file(vel))
            rpm_err = (self.rpm0 - contents['rpm']) / contents['rpm']


# Inherits from the ConstantPower class. Evaluates the performance of a constant pitch propeller at various velocities
class ConstantRPM(ConstantPitchPropeller):
    # rpm: rpm the propeller will spin at
    def __init__(self, rpm, geom, vel, bend=False, fluid=None, out_folder=None):
        out_folder = os.path.join('out', f'{geom.name}_rpm') if out_folder is None else out_folder
        super().__init__(geom, vel, bend, fluid, out_folder)
        self.const_rpm = rpm

    def eval_vel(self, vel):
        solvers = ['GRAD', 'POT', 'VRTX']
        solv = solvers.pop()

        self._run_vel(vel, self.const_rpm, solv)
        contents = file_tools.extract_aero(self._aero_file(vel))
        while not contents['converged']:
            if solvers:
                solv = solvers.pop()
            else:
                break
            self._run_vel(vel, self.const_rpm, solv)
            contents = file_tools.extract_aero(self._aero_file(vel))


# for a variable pitch constant power propeller design. Inherits from ConstantPower
class VariablePitch(ConstantPitchPropeller):
    def __init__(self, power, offsets, geom, vel, bend=False, fluid=None, out_folder=None, rpm0=200):
        self.geom = geom
        self.bend = bend
        self.power = power

        self.bend_data = pd.DataFrame()
        self.race_data = pd.DataFrame()
        self.aero_data = pd.DataFrame()
        self.aero_data_all = None
        self.bend_data_all = None

        # default fluid to characteristics of water
        if fluid is None:
            self.fluid = {'density': 1000,
                          'kinematic_viscosity': 10**-6,
                          'speed_sound': 10**5
                          }
        else:
            self.fluid = fluid

        self.out_folder = os.path.join('out', f'{self.geom.name}_VPP') if out_folder is None else out_folder
        make_folder(self.out_folder)
        self.const_folder = os.path.join(self.out_folder, 'const')
        self.aero_plots = os.path.join(self.out_folder, 'aero_plots')
        self.bend_plots = os.path.join(self.out_folder, 'bend_plots')

        # creates a ConstantPower object for each angle in offset_list
        self.const_props = {}
        for off in offsets:
            constant_out = os.path.join(self.const_folder, f'{off:.2f}')
            make_folder(self.const_folder)
            offset_geometry = geom.create_offset(off)
            self.const_props[f'{off:.3f}'] = ConstantPower(self.power, offset_geometry, vel,
                                                           bend, fluid, constant_out, rpm0)

    # returns the plot file name
    def _aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def _bend_plot_file(self, name):
        return os.path.join(self.bend_plots, name)

    # evaluates the aerodynamic data for each ConstantPower design
    def eval_performance(self, verbose=False):
        clear_path(self.out_folder)
        make_folder(self.out_folder)
        make_folder(self.const_folder)
        for prop in self.const_props.values():
            prop.eval_performance(verbose)

    # compiles all the XROTOR output files
    def compile_data(self):
        aero_data = []
        bend_data = []
        for off, prop in self.const_props.items():
            prop.compile_data()

            prop.aero_data['angle_offset'] = [off for _ in range(len(prop.aero_data))]
            aero_data.append(prop.aero_data)

            if self.bend:
                prop.bend_data['angle_offset'] = [off for _ in range(len(prop.bend_data))]
                bend_data.append(prop.bend_data)

        self.aero_data_all = pd.concat(aero_data, axis=0, ignore_index=True)
        if self.bend:
            self.bend_data_all = pd.concat(bend_data, axis=0, ignore_index=True)
        self._get_ideal()

    def _get_ideal(self):
        vpp_inds = self.aero_data_all.groupby('vel')['thrust'].idxmax()
        self.aero_data = self.aero_data_all.loc[vpp_inds, :]
        if self.bend:
            for _, row in self.aero_data.iterrows():
                bend_mask = (self.bend_data_all['vel'] == row['vel']) & \
                            (self.bend_data_all['angle_offset'] == row['angle_offset'])
                self.bend_data = self.bend_data.append(self.bend_data_all[bend_mask])

    def plot_aero(self, *names, save=False, disp=False):
        for name in names:
            graphing.vpp_plot(self.aero_data, self.aero_data_all, name)
            if save:
                make_folder(self.aero_plots)
                plt.savefig(self._aero_plot_file(name))
            display_plot(disp)

    def plot_struct(self, *names, save=False, disp=False):
        for name in names:
            graphing.single_struct_plot(name, self.bend_data)
            if save:
                make_folder(self.bend_plots)
                plt.savefig(self._bend_plot_file(name))
            display_plot(disp)


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
