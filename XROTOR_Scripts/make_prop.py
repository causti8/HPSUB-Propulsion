import numpy as np
import copy
import os


# defines the path to airfoil aerodynamic performance files
def aero_path(foil):
    return os.path.join('airfoils', f'{foil}.txt')


# defines the path to the propeller geometry files
def propeller_path(propeller):
    return os.path.join('propellers', f'{propeller}.txt')


# defines the path to airfoil structural files
def structural_path(foil):
    return os.path.join('structural', f'{foil}.txt')


# a class made to contain all the information necessary to define a propeller shape. Made to contain airfoil structural
# and aerodynamic performance information necessary for XROTOR
# num_sections: the number of radial sections used to define propeller
class PropGeom:
    def __init__(self, propeller_file):
        r_over_r = []
        c_over_r = []
        foil_names = []
        beta = []
        with open(propeller_path(propeller_file)) as file:
            self.diam = float(next_line(file))
            self.hub_diam = float(next_line(file))
            self.blades = int(next_line(file))
            for line in file:
                if line[0] is not '#':
                    line_arr = line.split()
                    r_over_r.append(float(line_arr[0]))
                    c_over_r.append(float(line_arr[1]))
                    foil_names.append(line_arr[2])
                    beta.append(float(line_arr[3]))
        self.num_sections = len(beta)
        self.r_over_r = np.array(r_over_r, dtype=float)
        self.c_over_r = np.array(c_over_r, dtype=float)
        self.foil_names = np.array(foil_names, dtype=str)
        self.beta = np.array(beta, dtype=float)

        # 3 keys: 'density', 'elastic_modulus', 'poissons'
        self.material = None
        # list of Foil objects at each radial location. Handles each airfoils performance information.
        self.foil_aero = []
        # list of airfoil structural property objects at each radial location
        self.foil_bend = []

    # compiles aerodynamic data for each airfoil on the propeller.
    def init_aero(self):
        for i in range(self.num_sections):
            self.foil_aero.append(FoilAero(aero_path(self.foil_names[i])))

    # sets the Reynolds number at each airfoil along the blade
    def set_re_blade(self, v, rpm, nu):
        omega = rpm * (np.pi/30)
        vt = omega * self.r_over_r * self.diam / 2
        v_total = np.sqrt(v**2 + vt**2)
        chord = self.c_over_r * self.diam / 2
        reynolds = v_total*chord/nu
        for i, re in enumerate(reynolds):
            self.foil_aero[i].set_re(re)

    # creates a copy of the geometry object, but with an offset angle distribution. Made for VPP design
    def create_offset(self, offset):
        prop = copy.deepcopy(self)
        prop.beta = prop.beta + offset
        return prop

    # compiles structural data for each airfoil on the propeller.
    # material: dictionary with 3 keys: 'density', 'elastic_modulus', and 'poissons'
    def init_structural(self, material):
        self.material = material
        for i in range(self.num_sections):
            self.foil_bend.append(FoilStruct(self.foil_names[i]))
            self.foil_bend[i].set_material(material['density'], material['elastic_modulus'], material['poissons'])
            self.foil_bend[i].set_chord(self.r_over_r[i] * self.diam / 2, self.c_over_r[i] * self.diam / 2)

    # writes out a file of the propellers structural properties in the format XROTOR wants
    def write_structural(self, file_name):
        with open(file_name, 'w') as file:
            file.write('\n')
            file.write('structural\n')
            file.write('   R      EIout     EIin     EA       GJ        EK       m'
                       '       MXX     xCG/c    xSC/C     rST \n')

            for section in self.foil_bend:
                rounded_dict = format_dictionary(section.main_dict)
                file.write(
                           f"{rounded_dict['R']} {rounded_dict['EIout']} {rounded_dict['EIin']} "
                           f"{rounded_dict['EA']} {rounded_dict['GJ']} {rounded_dict['EK']} "
                           f"{rounded_dict['M']} {rounded_dict['MXX']} {rounded_dict['XOCG']} "
                           f"{rounded_dict['XOSC']} {rounded_dict['RST']}\n"
                           )


# Class handles airfoil aerodynamic performance information
class FoilAero:
    def __init__(self, foil_file):
        # dictionary of the airfoil performance at current reynolds number
        self.performance = {}
        # list of dictionaries containing airfoil performance at several different reynolds numbers
        self.foil_data = []

        with open(foil_file) as f:
            f.readline()
            for line in f:
                line_array = line.split()
                line_dict = {
                    'reference Re number': float(line_array[0]),
                    'zero-lift alpha(deg)': float(line_array[1]),
                    'd(Cl)/d(alpha)': float(line_array[2]),
                    'd(Cl)/d(alpha)@Stall': float(line_array[3]),
                    'maximum Cl': float(line_array[4]),
                    'minimum Cl': float(line_array[5]),
                    'Cl increment to stall': float(line_array[6]),
                    'Cm': float(line_array[7]),
                    'minimum Cd': float(line_array[8]),
                    'Cl at minimum Cd': float(line_array[9]),
                    'd^2(Cd)/d^2(Cl)': float(line_array[10]),
                    'Re scaling exponent': float(line_array[11]),
                    'critical mach': float(line_array[12])
                }
                self.foil_data.append(line_dict)

    # sets performance to contain data from the proper reynolds number
    def set_re(self, re):
        for dictionary in self.foil_data:
            self.performance = None
            if dictionary['reference Re number'] > re:
                self.performance = dictionary
                break

        if self.performance is None:
            self.performance = self.foil_data[-1]


# Class contains contains all of the information necessary to evaluate the bending, and stress of a propeller through
# XROTOR
class FoilStruct:
    # airfoil: the name of the airfoil
    def __init__(self, airfoil):
        with open(structural_path(airfoil)) as file:
            # dictionary containing all the information from a foil structural file
            self.file_dict = {}
            self.file_dict.update({'A': get_third(file.readline())})
            self.file_dict.update({'IYY': get_third(file.readline())})
            self.file_dict.update({'IXX': get_third(file.readline())})
            self.file_dict.update({'J': get_third(file.readline())})
            self.file_dict.update({'XOCG': get_third(file.readline())})
            self.file_dict.update({'RST': get_third(file.readline())})

            # dictionary of structural information with material and chord length taken into account
            self.main_dict = {}

    # sets the material of the airfoil section
    def set_material(self, rho, elastic_modulus, poissons_ratio):
        shear_modulus = elastic_modulus / (2 * (1+poissons_ratio))
        self.main_dict.update({'EIin': elastic_modulus * self.file_dict['IXX']})
        self.main_dict.update({'EIout': elastic_modulus * self.file_dict['IYY']})
        self.main_dict.update({'EA': elastic_modulus * self.file_dict['A']})
        self.main_dict.update({'GJ': shear_modulus * self.file_dict['J']})
        self.main_dict.update({'EK': 0})
        self.main_dict.update({'M': rho * self.file_dict['A']})
        self.main_dict.update({'MXX': 0})
        self.main_dict.update({'XOCG': self.file_dict['XOCG']})
        self.main_dict.update({'XOSC': self.file_dict['XOCG']})
        self.main_dict.update({'RST': self.file_dict['RST']})

    # sets the chord length of the airfoil section
    # radius: radial location of section
    # chord: chord length of section
    def set_chord(self, radius, chord):
        self.main_dict.update({'R': radius})
        self.main_dict['EIin'] = chord**4 * self.main_dict['EIin']
        self.main_dict['EIout'] = chord**4 * self.main_dict['EIout']
        self.main_dict['EA'] = chord**2 * self.main_dict['EA']
        self.main_dict['GJ'] = chord**4 * self.main_dict['GJ']
        self.main_dict['M'] = chord**2 * self.main_dict['M']
        self.main_dict['RST'] = chord * self.file_dict['RST']


# makes sure to skip over lines with # at the start
def next_line(file):
    line = file.readline()
    while line[0] == '#':
        line = file.readline()
    return line


# creates a new dictionary from a float dictionary that turns each value into a rounded string
def format_dictionary(data):
    string_data = {}
    for key, value in data.items():
        string_data.update({key: f"{value:.2E}"})
    return string_data


# returns the third token in a string. Used for reading structural files
def get_third(line):
    array = line.split()
    return float(array[3])
