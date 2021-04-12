import os
import shutil
import numpy as np


# extracts the data from a XROTOR aerodynamic output file
def extract_aero(file_name):
    data = {'converged': True}
    with open(file_name, 'r') as f:
        for line in f:
            if 'NOT CONVERGED' in line:
                data['converged'] = False
            if 'radius' in line:
                _, data['rad'], _ = remove_words(line)
            if 'thrust' in line:
                data['thrust'], data['power'], data['torque'] = remove_words(line)
            if 'Efficiency' in line:
                data['efficiency'], data['vel'], data['rpm'] = remove_words(line)
            if 'Eff ideal' in line:
                _, data['efficiency_ideal'], _ = remove_words(line)

    def safe_float(word):
        try:
            return float(word)
        except:
            return np.NaN


# takes in a line from an aerodynamic file and parses the line into 3 numbers
def safe_float(word):
    try:
        return float(word)
    except ValueError:
        return np.NaN


def remove_words(line):
    token_1 = safe_float(line[14:28].strip())
    token_2 = safe_float(line[40:54].strip())
    token_3 = safe_float(line[66:-1].strip())
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
        self.von_misses = np.zeros(num_sections)

        self.data_top = {
            "r_over_r": np.zeros(num_sections),
            "forward_displacement": np.zeros(num_sections),
            "tangent_displacement": np.zeros(num_sections),
            "torsional_displacement": np.zeros(num_sections),
            "forward_moment": np.zeros(num_sections),
            "tangent_moment": np.zeros(num_sections),
            "torsion": np.zeros(num_sections),
            "spanwise_force": np.zeros(num_sections),
            "forward_force": np.zeros(num_sections),
            "tangent_force": np.zeros(num_sections)
        }

        self.data_bottom = {
            "strain_xx": np.zeros(num_sections),
            "strain_zz": np.zeros(num_sections),
            "strain_yy": np.zeros(num_sections),
            "strain_max": np.zeros(num_sections),
            "strain_xz": np.zeros(num_sections),
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

    # calculates the von-misses stress at each section
    def calc_stress(self, elastic_modulus, poissons_ratio):
        zipped_arrays = zip(range(len(self.von_misses)), self.data_bottom['strain_xx'], self.data_bottom['strain_yy'],
                            self.data_bottom['strain_zz'], self.data_bottom['strain_xz'])

        for i, sxx, syy, szz, sxz in zipped_arrays:
            stiffness_matrix = make_stiff_3d(elastic_modulus, poissons_ratio)
            strain_vector = np.array([[sxx, syy, szz, 0, sxz, 0]]).T

            stress_vector = stiffness_matrix @ strain_vector

            self.von_misses[i] = calc_von_misses(stress_vector)


# function to create a 3d stiffness matrix
def make_stiff_3d(elastic_modulus, poissons_ratio):
    stiffness_matrix = np.zeros([6, 6])
    stiffness_matrix[0:3, 0:3] = poissons_ratio * np.ones([3, 3]) + (1 - 2 * poissons_ratio) * np.eye(3)
    stiffness_matrix[3:6, 3:6] = (1 - 2 * poissons_ratio) * np.eye(3)
    stiffness_matrix = elastic_modulus / ((1 + poissons_ratio) * (1 - 2 * poissons_ratio)) * stiffness_matrix
    return stiffness_matrix


# function finds the von-mises stress from a stress vector
def calc_von_misses(stress_vector):
    term1 = (stress_vector[0] - stress_vector[1])**2 + \
            (stress_vector[1] - stress_vector[2])**2 + \
            (stress_vector[2] - stress_vector[0])**2
    term2 = stress_vector[3]**2 + stress_vector[4]**2 + stress_vector[5]**2
    return np.sqrt(0.5*term1) + np.sqrt(3*term2)


def overwrite(file):
    if os.path.isfile(file):
        os.remove(file)


def clear_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def make_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
