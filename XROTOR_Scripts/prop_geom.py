import numpy as np
import copy
import os
import pandas as pd


class PropGeom:
    def __init__(self, propeller_file=None, material=None):
        self.name = propeller_file
        if propeller_file is not None:
            self.sections = pd.read_csv(geom_path(propeller_file), skiprows=2)
            first_lines = pd.read_csv(geom_path(propeller_file), nrows=2)
            diam, hub_diam, blades = first_lines.loc[0][:3]
            self.diam, self.hub_diam, self.blades = float(diam), float(hub_diam), int(blades)

            foil_list = []
            for name in set(self.sections['airfoil']):
                foil = pd.read_csv(aero_path(name))
                foil['name'] = [name for _ in range(len(foil))]
                foil_list.append(foil)
            self.foil_data = pd.concat(foil_list, axis=0, ignore_index=True)
            self.curr_aero = None
        else:
            self.sections = None
            self.foil_data = None
            self.diam, self.hub_diam, self.blades = None, None, None

        self.material = material
        if material is not None:
            self._set_bend(material)
        else:
            self.bend_data = None

    # sets the Reynolds number at each airfoil along the blade
    def set_aero(self, v, rpm, nu, speed_sound):
        self.curr_aero = pd.DataFrame()
        chord = self.sections['chord_ratio'] * self.diam/2
        radius = self.sections['rad_ratio'] * self.diam/2
        self.curr_aero['re'] = calc_re(v, rpm, nu, chord, radius)
        self.curr_aero['r'] = list(map(r_eqn, self.curr_aero['re']))
        self._foil_perf()

    def _foil_perf(self):
        curr_aero = []
        for i, row in self.sections.iterrows():
            foil = self.foil_data[self.foil_data['name'] == row['airfoil']]
            ind = (abs(foil['ref_re'] - self.curr_aero.loc[i, 're'])).idxmin()
            curr_aero.append(foil.loc[ind, :].to_dict())
        self.curr_aero = self.curr_aero.join(pd.DataFrame(curr_aero))

    def _set_bend(self, material):
        bend_data = []
        el = material['elastic_modulus']
        rho = material['density']
        shear_mod = material['elastic_modulus'] / (2 * (1+material['poissons']))
        for _, sec in self.sections.iterrows():
            file = pd.read_csv(structural_path(sec['airfoil']))
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
        self.curr_aero.to_csv(file_name, float_format='%.4E', index=False)

    # creates a copy of the geometry object, but with an offset angle distribution. Made for VPP design
    def create_offset(self, offset):
        prop = copy.deepcopy(self)
        prop.sections['pitch'] = self.sections['pitch'] + offset
        return prop


def calc_re(v, rpm, nu, chord, radius):
    v_mag = blade_vel(v, rpm, radius)
    return v_mag*chord / nu


def blade_vel(v, rpm, radius):
    omega = rpm * (np.pi / 30)
    vt = omega * radius
    return np.sqrt(v ** 2 + vt ** 2)


def r_eqn(reynolds):
    if reynolds > 2e6:
        return -0.15
    elif reynolds > 2e5:
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
