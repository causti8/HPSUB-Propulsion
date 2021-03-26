import numpy as np
import make_prop
import designs
import speed_calculations
import matplotlib.pyplot as plt


geometry = make_prop.PropGeom('Prop_1')
geometry.init_aero()         # gets airfoil performance data from airfoil_data folder

aluminum = {
    'density': 2710,
    'elastic_modulus': 69e9,
    'poissons': 0.3
}

geometry.init_structural(aluminum)   # sets the structural information about airfoil


a = np.linspace(0.1, 2.5, 5)
b = np.linspace(2.6, 3.2, 30)
c = np.linspace(3.2, 3.5, 4)

vel_aero = np.concatenate((a, b, c), axis=0)

eval_structural = np.zeros(len(vel_aero), dtype=bool)
eval_structural[0:3] = True

water = {'density': 1000,
         'viscosity': 1e-6,
         'speed_sound': 1500
         }

# Constant Power Design
# '''

geometry.beta = geometry.beta+10

pwr = 300
design_pwr = designs.ConstantPower(geometry, pwr, vel_aero, 'out\\ConstPwr', eval_structural, rpm0=300)

# '''
design_pwr.evaluate_performance()
design_pwr.compile_data()

design_pwr.plot_aero('thrust', save=True)
design_pwr.plot_aero('torque', save=True)
design_pwr.plot_aero('efficiency', save=True)
design_pwr.plot_aero('RPM', save=True)
design_pwr.plot_aero('coefficients', save=True)

design_pwr.plot_struct('von_misses', save=True)
# '''

# Constant RPM Design
'''
rpm = 400
design_rpm = designs.ConstantRPM(geometry, rpm, vel_aero, 'out\\ConstantRPM', eval_structural, water)

design_rpm.evaluate_aero()
design_rpm.compile_data()

design_rpm.plot_aero('thrust', save=True)
design_rpm.plot_aero('torque', save=True)
design_rpm.plot_aero('efficiency', save=True)
design_rpm.plot_aero('RPM', save=True)
design_rpm.plot_aero('coefficients', save=True)

design_rpm.plot_struct('von_misses', save=True)
'''

# Constant Power Variable Pitch Design
'''
power = 300
offset_list = np.linspace(-10, 10, 6)
design_vpp = designs.VariablePitch(geometry, power, vel_aero, offset_list,
                                   'out\\VPP', eval_structural, fluid=None, rpm0=6000)

design_vpp.evaluate_aero()
design_vpp.compile_data()

design_vpp.plot_aero('thrust', save=True)
design_vpp.plot_aero('torque', save=True)
design_vpp.plot_aero('efficiency', save=True)
design_vpp.plot_aero('RPM', save=True)
design_vpp.plot_aero('coefficients', save=True)

design_vpp.plot_struct('von_misses', save=True)
'''

# Speed Prediction plot
# '''
drag_coef = 0.04
frontal_area = 0.2636
sub_mass = 400.2

initial_gate = 42
final_gate = 50

# any of the design objects, drag coefficient, frontal area of sub, and sub mass
speed_pwr = speed_calculations.RaceSpeed(design_pwr, drag_coef, frontal_area, sub_mass)
speed_pwr.find_recorded_speed(initial_gate, final_gate, write=False)
speed_pwr.plot(save=True)

# '''
