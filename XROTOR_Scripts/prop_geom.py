import numpy as np
import copy
import os
import pandas as pd


# a class made to contain all the information necessary to define a propeller shape. Made to contain airfoil structural
# and aerodynamic performance information necessary for XROTOR
# num_sections: the number of radial sections used to define propeller
def best_re(foil_data, re):
    min_dif = abs(foil_data['ref_re'][0] - re)
    closest_row = foil_data.iloc[0]
    for _, row in foil_data.iterrows():
        if abs(row['ref_re'] - re) < min_dif:
            min_dif = abs(row['ref_re'] - re)
            closest_row = row
    return closest_row


class PropGeom:
    def __init__(self, propeller_file=None, material=None):
        if propeller_file is not None:

            # reads the sections data from csv
            self.sections = pd.read_csv(geom_path(propeller_file), skiprows=2)

            # reads the diam, hub_diam and blades from csv
            first_lines = pd.read_csv(geom_path(propeller_file), nrows=2)
            diam, hub_diam, blades = first_lines.loc[0][:]
            self.diam, self.hub_diam, self.blades = float(diam), float(hub_diam), int(blades)

            # creates a dataframe containing all the airfoil aerodynamic data
            airfoil_data = pd.DataFrame()
            for name in set(self.sections['airfoil']):
                airfoil_data.append(pd.read_csv(aero_path(name)))
            self.curr_aero = None
        else:
            self.size, self.sections, = None, None

        if material is not None:
            self._set_bend(material)
        else:
            self.bend_data = None

    # sets the Reynolds number at each airfoil along the blade
    def set_aero(self, v, rpm, nu, speed_sound):
        reynolds = self._calc_re(v, rpm, nu)
        curr_aero = []

        for foil, re in zip(self.aero_frames, reynolds):
            curr_aero.append(best_re(foil, re))
        self.curr_aero = pd.DataFrame(curr_aero)

        self.curr_aero['re_actual'] = reynolds
        self.curr_aero['r'] = list(map(r_eqn, reynolds))
        self.curr_aero['mach'] = self._calc_mach(v, rpm, speed_sound)

    def _calc_mach(self, v, rpm, speed_sound):
        v_mag = self._blade_vel(v, rpm)
        return v_mag / speed_sound

    def _calc_re(self, v, rpm, nu):
        v_mag = self._blade_vel(v, rpm)
        chord = self.sections['chord_ratio'].to_numpy() * self.diam/2
        return v_mag*chord / nu

    def _blade_vel(self, v, rpm):
        omega = rpm * (np.pi / 30)
        vt = omega * self.sections['rad_ratio'].to_numpy() * self.diam / 2
        return np.sqrt(v ** 2 + vt ** 2)

    def _set_bend(self, material):
        bend_data = []
        el = material['elastic_modulus']
        rho = material['density']
        shear_mod = material['elastic_modulus'] / (2*(1+material['poissons']))
        for _, sec in self.sections.iterrows():
            file = pd.read_csv(structural_path(sec['foil_name']))
            bend = file.iloc[0]
            a = {
                'r': sec['rad_ratio'] * self.diam/2,
                'ei_out': el * bend['i_xx'] * sec['chord_ratio']**4,
                'ei_in': el * bend['i_yy'] * sec['chord_ratio']**4,
                'ea': el * bend['area'] * sec['chord_ratio']**2,
                'gj': shear_mod * bend['j'] * sec['chord_ratio']**4,
                'ek': 0,
                'm': rho * bend['area'] * sec['chord_ratio']**2,
                'mxx': 0,
                'xcg': bend['centroid'],
                'xsc': bend['centroid'],
                'rst': bend['max_y'] * sec['chord_ratio'],
            }
            bend_data.append(a)
        self.bend_data = pd.DataFrame(bend_data)

    def write_bend(self, file_name):
        self.bend_data.to_csv(file_name, sep='\t', float_format='%.4E', index=False)

    def write_aero(self, file_name):
        self.curr_aero.to_csv(file_name, float_format='%.4E')

    # creates a copy of the geometry object, but with an offset angle distribution. Made for VPP design
    def create_offset(self, offset):
        prop = copy.deepcopy(self)
        prop.sections['pitch'] = self.sections['pitch'] + offset
        return prop


def r_eqn(reynolds):
    if reynolds > 2e6:
        return -0.15
    elif reynolds > 200:
        return -1
    else:
        return -0.5

# defines the path to airfoil aerodynamic performance files
def aero_path(foil):
    return os.path.join('airfoils', f'{foil}.csv')


# defines the path to the propeller geometry files
def geom_path(propeller):
    return os.path.join('propellers', f'{propeller}.csv')


# defines the path to airfoil structural files
def structural_path(foil):
    return os.path.join('airfoils_bend', f'{foil}.csv')