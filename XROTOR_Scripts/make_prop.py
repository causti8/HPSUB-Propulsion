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
    def __init__(self, propeller_file=None):
        r_over_r = []
        c_over_r = []
        foil_names = []
        beta = []

        if propeller_file is not None:
            with open(propeller_path(propeller_file)) as file:
                self.diam = float(next_line(file))
                self.hub_diam = float(next_line(file))
                self.blades = int(next_line(file))
                for line in file:
                    if line[0] != '#':
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
        self.name = propeller_file

        # 3 keys: 'density', 'elastic_modulus', "poisson's"
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
            self.foil_bend[i].set_material(material['density'], material['elastic_modulus'], material["poisson's"])
            self.foil_bend[i].set_chord(self.r_over_r[i] * self.diam / 2, self.c_over_r[i] * self.diam / 2)

    # writes out a file of the propellers structural properties in the format XROTOR wants
    def write_structural(self, file_name):
        with open(file_name, 'w') as file:
            file.write('\n')
            file.write('structural\n')
            file.write('   R      EIout     EIin     EA       GJ        EK       m'
                       '       MXX     xCG/c    xSC/C     rST \n')

            mat = dict_to_mat(self.foil_bend)
            mat = interp_colm(mat)

            for section in range(mat.shape[0]):
                for j in range(mat.shape[1]):
                    file.write('  {:.2e}  '.format(mat[section, j]))
                file.write('\n')


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
            self.A = get_third(file.readline())
            self.IYY = get_third(file.readline())
            self.IXX = get_third(file.readline())
            self.J = get_third(file.readline())
            self.XOCG = get_third(file.readline())
            self.RST = get_third(file.readline())

    # sets the material of the airfoil section
    def set_material(self, rho, elastic_modulus, poissons_ratio):
        shear_modulus = elastic_modulus / (2 * (1+poissons_ratio))
        self.EIin = elastic_modulus * self.IXX
        self.EIout = elastic_modulus * self.IYY
        self.EA = elastic_modulus * self.A
        self.GJ = shear_modulus * self.J
        self.EK = 0
        self.M = rho * self.A
        self.MXX = 0
        self.mXOCG = self.XOCG
        self.XOSC = self.XOCG
        self.RST = self.RST

    # sets the chord length of the airfoil section
    # radius: radial location of section
    # chord: chord length of section
    def set_chord(self, radius, chord):
        self.R = radius
        self.EIin = chord**4 * self.EIin
        self.EIout = chord**4 * self.EIout
        self.EA = chord**2 * self.EA
        self.GJ = chord**4 * self.GJ
        self.M = chord**2 * self.M
        self.RST = chord * self.RST


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


def dict_to_mat(data):
    mat = []
    for section in data:
        vect = [section.R, section.EIout, section.EIin, section.EA, section.GJ, section.EK, section.M, section.MXX,
                section.XOCG, section.XOSC, section.RST]
        mat.append(vect)
    mat = np.array(mat)
    return mat


def interp_colm(mat):
    SECTIONS = 30
    _, colm_count = mat.shape
    new_mat = np.zeros([SECTIONS, colm_count])

    rr = np.linspace(mat[0, 0], mat[-1, 0], SECTIONS, endpoint=True)
    new_mat[:, 0] = rr
    for colm in range(1, colm_count):
        new_mat[:, colm] = np.interp(rr, mat[:, 0], mat[:, colm])
    return new_mat


# returns the third token in a string. Used for reading structural files
def get_third(line):
    array = line.split()
    return float(array[3])
