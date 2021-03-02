import os
import math
import numpy as np
import shutil
import fit_graphing
from scipy import stats
import matplotlib.pyplot as plt


def analyze_airfoil(airfoil_name, re_list=None, alpha_range=None, fit_bounds=None, naca=False, pane=None):
    if fit_bounds is None:
        fit_bounds = np.array([-2, 6])
    if alpha_range is None:
        alpha_range = [-15, 15, 0.5]

    fit_bounds = np.array(fit_bounds)
    # opens file to store xrotor data in
    folder = PathManager(airfoil_name)
    data = initialize_data()

    with open(overwrite_file(folder.data_file()), "w") as f:
        write = WriteFile(f)

        write(" ref_Re      0-lift     dcl/da  dcl/da@stall  cl_max      "
              "cl_min   dCL@stall    cm_avg     min Cd    CL@CDmin     CD2         r         mach")

        positive_range = [0, alpha_range[1], alpha_range[2]]
        negative_range = [-alpha_range[2], alpha_range[0], alpha_range[2]]

        for re in re_list:
            if re > 2e6:
                data['Re scaling exponent'] = -0.15
            elif re > 2e5:
                data['Re scaling exponent'] = -0.75
            else:
                data['Re scaling exponent'] = -0.4

            data['reference Re number'] = re
            xfoil_run(folder, airfoil_name, positive_range, re, naca, pane)
            positive_array = np.loadtxt(folder.xfoil_outfile(), skiprows=12)
            xfoil_run(folder, airfoil_name, negative_range, re, naca, pane)
            negative_array = np.loadtxt(folder.xfoil_outfile(), skiprows=12)

            # extracts the data from positive polar
            if len(negative_array) < 1 or len(positive_array) < 1:
                raise Exception(f"Failed to converge at Re:{re}")
            alpha, cl, cd, cm = combine_arrays(negative_array, positive_array)

            # Creates a fit for that data
            fit_data(alpha, cl, cd, cm, fit_bounds, data)
            stall_angle(alpha, cl, cd, data)

            # Writes data out to a file
            write_data(write, data)

            folder.re = re
            fit_graphing.plot_graphs(folder, alpha, cl, cd, cm, data)


def xfoil_run(folder, airfoil, alpha_range, re, naca, pane):
    max_iter = 100
    # create input file
    with open(overwrite_file(folder.xfoil_infile()), 'w') as inFile:
        write = WriteFile(inFile, verbose=True)

        # loads the data-points
        if naca:
            write(f"NACA {airfoil}")
        else:
            write(f"LOAD {folder.coordinate_file()}")

        # Sets the number of panels to be used

        if pane is not None:
            write("PPAR")
            write(f"N {pane}")
            write('')
            write('')
        write('PANE')

        # enters the operation section
        write("OPER")
        write("ITER 100")
        # sets the solver to viscous at set reynolds number
        write(f"VISC {re}")
        # sets the max number of iterations to be used
        # write(f"iter {max_iter}")

        # Sets up the polar file
        write("SEQP")
        write("PACC")
        write(overwrite_file(folder.xfoil_outfile()))
        write('')
        # Runs the range of alphas
        alpha_input = f"{alpha_range[0]} {alpha_range[1]} {alpha_range[2]}"
        write(f"aSEQ {alpha_input}")
        write("dump.txt")

        # closes x-foil
        write('')
        write("quit")
    # runs the input file through x-foil
    os.system(f"{os.path.join('bin', 'xfoil.exe')} < {folder.xfoil_infile()}")


def combine_arrays(negative_array, positive_array):
    # extracts the data from negative polar
    alpha_neg = np.flip(negative_array[:, 0])
    cl_neg = np.flip(negative_array[:, 1])
    cd_neg = np.flip(negative_array[:, 2])
    cm_neg = np.flip(negative_array[:, 4])

    # extracts the data from positive polar
    alpha_pos = positive_array[:, 0]
    cl_pos = positive_array[:, 1]
    cd_pos = positive_array[:, 2]
    cm_pos = positive_array[:, 4]

    # combines the negative and positive data
    alpha = deg_to_rad(np.concatenate((alpha_neg, alpha_pos), axis=0))
    cl = np.concatenate((cl_neg, cl_pos), axis=0)
    cd = np.concatenate((cd_neg, cd_pos), axis=0)
    cm = np.concatenate((cm_neg, cm_pos), axis=0)
    return alpha, cl, cd, cm


def fit_data(alpha, cl, cd, cm, fit_bounds, data):
    # put fit bounds in radians
    fit_bounds = deg_to_rad(fit_bounds)

    # indices corresponding to the bounds
    is_above = alpha > fit_bounds[0]
    is_below = alpha < fit_bounds[1]
    bottom_bound_ind = first_true(is_above)
    top_bound_ind = last_true(is_below)

    fit_range_ind = range(bottom_bound_ind, top_bound_ind)

    m, b, _, _, _ = stats.linregress(alpha[fit_range_ind], cl[fit_range_ind])
    data['d(Cl)/d(alpha)'] = m
    data['zero-lift angle(deg)'] = rad_to_deg(-b/m)

    a, b, c = np.polyfit(cl[fit_range_ind], cd[fit_range_ind], 2)

    data['minimum Cd'] = c - b**2/(4*a)
    data['Cl at minimum Cd'] = -b/(2*a)
    data['(1/2)d^2(Cd)/d^2(Cl)'] = a

    data['Cm'] = np.mean(cm[fit_range_ind])


def stall_angle(alpha, cl_actual, cd_actual, data):
    stall_xtr = 0.005
    # finds the predicted cl and cd from data fits
    cd_predicted = data['(1/2)d^2(Cd)/d^2(Cl)'] * (cl_actual - data['Cl at minimum Cd']) ** 2 + data['minimum Cd']

    ind_min, ind_max = bounds_above(abs(cd_actual-cd_predicted), stall_xtr)
    data['minimum Cl'] = cl_actual[ind_min]
    data['maximum Cl'] = cl_actual[ind_max]
    data['Cl increment to stall'] = max(cl_actual) - data['maximum Cl']

    if alpha[np.argmax(cl_actual)] - alpha[ind_max] < 10**-6:
        data['d(Cl)/d(alpha) @stall'] = 1
    else:
        delta_alpha = alpha[np.argmax(cl_actual)] - alpha[ind_max]
        data['d(Cl)/d(alpha) @stall'] = data['Cl increment to stall'] / delta_alpha


def write_data(write, data):
    string_data = format_data(data)
    line = f"{string_data['reference Re number']}   {string_data['zero-lift angle(deg)']}   {string_data['d(Cl)/d(alpha)']}   "
    line += f"{string_data['d(Cl)/d(alpha) @stall']}   {string_data['maximum Cl']}   {string_data['minimum Cl']}  "
    line += f"{string_data['Cl increment to stall']}   {string_data['Cm']}   {string_data['minimum Cd']}   "
    line += f"{string_data['Cl at minimum Cd']}   {string_data['(1/2)d^2(Cd)/d^2(Cl)']}   {string_data['Re scaling exponent']}   "
    line += f"{string_data['Mcrit']}"
    write(line)


def initialize_data():
    data = {
        'zero-lift angle(deg)': 0,
        'd(Cl)/d(alpha)': 0,
        'd(Cl)/d(alpha) @stall': 0,
        'maximum Cl': 0,
        'minimum Cl': 0,
        'Cl increment to stall': 0,
        'minimum Cd': 0,
        'Cl at minimum Cd': 0,
        '(1/2)d^2(Cd)/d^2(Cl)': 0,
        'reference Re number': 0,
        'Re scaling exponent': 0,
        'Cm': 0,
        'Mcrit': 10
    }
    return data


def format_data(data):
    string_data = {}
    for key, value in data.items():
        string_data.update({key: f"{value:.2E}"})
    return string_data


class PathManager:
    def __init__(self, airfoil_name):
        self.airfoil_name = airfoil_name
        overwrite_path(self.performance_folder())
        self.re = 0

    def performance_folder(self):
        file = os.path.join('airfoil_data', f'{self.airfoil_name}')
        return file

    def coordinates_file(self):
        file = os.path.join('airfoil_coordinates', f'{self.airfoil_name}.dat')
        return file

    def coordinate_file(self):
        file = os.path.join('airfoil_coordinates', f'{self.airfoil_name}.dat')
        return file

    def data_file(self):
        folder = os.path.join(self.performance_folder(), 'XRotor_Data.txt')
        return folder

    def re_folder(self):
        folder = os.path.join(self.performance_folder(), f'{self.re:.2E}')
        return folder

    def xfoil_infile(self):
        file = os.path.join(self.performance_folder(), "infile.txt")
        return file

    def xfoil_outfile(self):
        file = os.path.join(self.performance_folder(), "outfile.txt")
        return file

    def cd_plot(self):
        file = os.path.join(self.re_folder(), "cd_plot.png")
        return file

    def cl_plot(self):
        file = os.path.join(self.re_folder(), "cl_plot.png")
        return file

    def cm_plot(self):
        file = os.path.join(self.re_folder(), "cm_plot.png")
        return file


class WriteFile:
    def __init__(self, file_obj, verbose=False):
        self.file = file_obj
        self.verbose = verbose

    def __call__(self, line):
        self.file.write(f'{line}\n')
        if self.verbose:
            print(line)


def bounds_above(array, min_value):
    inbound = array > min_value
    middle_ind = round(len(inbound) / 2)
    left_half = inbound[1:middle_ind]
    right_half = inbound[middle_ind:-1]
    return last_true(left_half), first_true(right_half)+middle_ind


def first_true(vector):
    for i, val in enumerate(vector):
        if val:
            return i
    return len(vector) - 1


def last_true(vector):
    for i in range(1, len(vector)+1):
        val = vector[len(vector)-i]
        if val:
            return len(vector) - i
    return 0


def overwrite_path(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def overwrite_file(file):
    if os.path.isfile(file):
        os.remove(file)
    return file


def find_index(vector, num):
    for i, val in enumerate(vector):
        if val > num:
            return i
    return len(vector)-1


def deg_to_rad(value):
    return (np.pi / 180) * value


def rad_to_deg(value):
    return (180 / np.pi) * value
