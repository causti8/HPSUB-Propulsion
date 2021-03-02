import os
import shutil
import numpy as np


# extracts the data from a XROTOR aerodynamic output file
class ExtractAero:
    def __init__(self, file_name):
        self.converged = True
        self.rad = 0
        self.T = 0
        self.pwr = 0
        self.Q = 0
        self.eff = 0
        self.vel = 0
        self.rpm = 0
        self.eff_ideal = 0
        with open(file_name, 'r') as f:
            for i, line in enumerate(f):
                if 'NOT CONVERGED' in line:
                    self.converged = False
                if 'radius' in line:
                    _, self.rad, _ = remove_words(line)
                if 'thrust' in line:
                    self.T, self.pwr, self.Q = remove_words(line)
                if 'Efficiency' in line:
                    self.eff, self.vel, self.rpm = remove_words(line)
                if 'Eff ideal' in line:
                    _, self.eff_ideal, _ = remove_words(line)


# takes in a line from an aerodynamic file and parses the line into 3 numbers
def remove_words(line):
    token_1 = float(line[14:28].strip()) if '*' not in line[14:28] else np.nan
    token_2 = float(line[40:54].strip()) if '*' not in line[40:54] else np.nan
    token_3 = float(line[66:-1].strip()) if '*' not in line[66:-1] else np.nan
    return token_1, token_2, token_3


# extracts the data from a XROTOR structural output file
class ExtractStructural:
    def __init__(self, file_name):
        # number of airfoil sections made by XROTOR
        num_sections = 30
        self.sxx = None
        self.syy = None
        self.szz = None
        self.sxy = None
        self.von_misses = None

        self.data_top = {
            "r_over_r": np.zeros(num_sections),
            "forward_displacement": np.zeros(num_sections),
            "tangent_displacement": np.zeros(num_sections),
            "torsional_displacement": np.zeros(num_sections),
            "forward_moment": np.zeros(num_sections),
            "self.tangent_moment": np.zeros(num_sections),
            "self.torsion": np.zeros(num_sections),
            "spanwise_force": np.zeros(num_sections),
            "forward_force": np.zeros(num_sections),
            "tangent_force": np.zeros(num_sections)
        }

        self.data_bottom = {
            "forward_strain": np.zeros(num_sections),
            "tangent_strain": np.zeros(num_sections),
            "spanwise_strain": np.zeros(num_sections),
            "max_strain": np.zeros(num_sections),
            "shear": np.zeros(num_sections)
        }

        with open(file_name) as file:
            # first 3 lines don't include data
            for _ in range(3):
                file.readline()

            # takes top section of data. Makes more sense if you look at a structural file
            for radial_section in range(num_sections):
                line_array = file.readline().split()
                for column, dict_name in enumerate(self.data_top.keys()):
                    self.data_top[dict_name][radial_section] = float(line_array[column + 1])

            # skips 2 lines that don't include data
            for _ in range(2):
                file.readline()

            # takes bottom section of data.
            for radial_section in range(num_sections):
                line_array = file.readline().split()
                for column, dict_name in enumerate(self.data_bottom.keys()):
                    self.data_bottom[dict_name][radial_section] = float(line_array[column + 2])

            # divides all data by 1000
            for dict_name in self.data_bottom.keys():
                self.data_bottom[dict_name] = self.data_bottom[dict_name] / 1000

    def calc_stress(self, elastic_modulus, poissons_ratio):
        self.sxx = (1 - poissons_ratio) * (self.data_bottom['forward_strain'] +
                    poissons_ratio * (self.data_bottom['tangent_strain'] + self.data_bottom['spanwise_strain']))
        self.sxx = (elastic_modulus / ((1+poissons_ratio) * (1-2*poissons_ratio))) * self.sxx

        self.syy = (1 - poissons_ratio) * (self.data_bottom['spanwise_strain'] +
                    poissons_ratio * (self.data_bottom['forward_strain'] + self.data_bottom['tangent_strain']))
        self.syy = (elastic_modulus / ((1+poissons_ratio) * (1-2*poissons_ratio))) * self.syy

        self.szz = (1 - poissons_ratio) * (self.data_bottom['tangent_strain'] +
                    poissons_ratio * (self.data_bottom['forward_strain'] + self.data_bottom['spanwise_strain']))
        self.szz = (elastic_modulus / ((1+poissons_ratio) * (1-2*poissons_ratio))) * self.szz

        self.sxy = (1-2*poissons_ratio) * self.data_bottom['shear']
        self.sxy = (elastic_modulus / ((1+poissons_ratio) * (1-2*poissons_ratio))) * self.sxy

        self.von_misses = von_misses(self.sxx, self.syy, self.szz, self.sxy)


# manages the folder hierarchy for the ConstantPower design class and ConstantRPM class
# - out_folder
#       - aero
#           - XROTOR aerodynamic output files
#       - structural
#           - XROTOR structural output files
#       - aero_plots
#           - aerodynamic performance plots
#       - struct_plots
#           - structural plots

class ConstantFolder:
    def __init__(self, out_folder):
        self.out_folder = out_folder
        self.aero_folder = os.path.join(self.out_folder, 'aero')
        self.aero_plots = os.path.join(self.out_folder, 'aero_plots')
        self.structural_folder = os.path.join(self.out_folder, 'structural')
        self.structural_plots = os.path.join(self.out_folder, 'structural_plots')
        self.speed_file = os.path.join(self.out_folder, 'max_speed.txt')
        self.structural_geometry = os.path.join(self.out_folder, 'structural_geom.txt')
        make_folder(self.out_folder)

    # resets everything. Called before creating new aerodynamic and structural data
    def reset_data(self):
        clear_path(self.out_folder)
        make_folder(self.out_folder)

    # returns a velocity file name
    def vel_file(self, vel):
        return os.path.join(self.aero_folder, f'{vel:.2f}.txt')

    # returns a structural file name
    def structural_file(self, vel):
        return os.path.join(self.structural_folder, f'{vel:.2f}.txt')

    # creates an aerodynamic plot file
    def aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def struct_plot_file(self, name):
        return os.path.join(self.structural_plots, name)


# manages the folder hierarchy for a variable pitch propeller
# - out_folder
#       - constant_pitch
#           - each angle offset
#               - velocity files
#       - structural
#           - constant_pitch
#               - each angle offset
#                   - velocity files
#       - aero_plots
#           - aerodynamic performance plots
#       - struct_plots
#           - structural plots

class VariableFolder:
    def __init__(self, out_folder):
        self.out_folder = out_folder
        self.const_folder = os.path.join(out_folder, 'constant_pitch')
        self.aero_plots = os.path.join(out_folder, 'aero_plots')
        self.structural_plots = os.path.join(out_folder, 'structural_plots')
        self.speed_file = os.path.join(out_folder, 'max_speed.txt')
        make_folder(out_folder)

    # resets the folders prior to evaluating new data
    def reset_data(self):
        clear_path(self.out_folder)
        make_folder(self.out_folder)

    # returns the plot file name
    def aero_plot_file(self, name):
        return os.path.join(self.aero_plots, name)

    # creates a structural plot file
    def struct_plot_file(self, name):
        return os.path.join(self.structural_plots, name)


def overwrite(file):
    if os.path.isfile(file):
        os.remove(file)


def clear_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def make_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)


def von_misses(sxx, syy, szz, sxy):
    term1 = (sxx-syy)**2 + (syy-szz)**2 + (szz-sxx)**2
    term2 = sxy**2
    return np.sqrt(0.5*term1) + np.sqrt(3*term2)