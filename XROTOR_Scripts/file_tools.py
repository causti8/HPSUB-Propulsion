import os
import shutil
import numpy as np
import pandas as pd


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


def extract_bend(file_name):
    new_file_name = file_name.replace('.txt', '.csv')
    convert_txt_to_csv(file_name, new_file_name)
    num_sections = 30
    data1 = pd.read_csv(new_file_name, skiprows=(0, 2), nrows=num_sections)
    return data1


# extracts the data from a XROTOR structural output file
# returns the data
def extract_structural(file_name):
    num_rows = 30
    new_name = file_name.replace('.txt', '.csv')
    convert_txt_to_csv(file_name, new_name)
    df1 = pd.read_csv(new_name, skiprow=2, nrows=num_rows)
    df2 = pd.read_csv(new_name, skiprows=num_rows+6)
    return df1.join(df2)


# calculates the von-misses stress at each section
def calc_stress(elastic_modulus, poissons_ratio):
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


def convert_txt_to_csv(in_filepath, out_filepath):
    with open(in_filepath, 'r') as in_f:
        with open(out_filepath, 'w') as out_f:
            for line in in_f:
                out_f.write(','.join(line.split()) + '\n')