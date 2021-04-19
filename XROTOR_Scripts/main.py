import numpy as np
import prop_geom
import designs
import matplotlib.pyplot as plt


aluminum = {
    'density': 2710,
    'elastic_modulus': 69e9,
    "poissons": 0.3
}

geom = prop_geom.PropGeom('prop_1', material=aluminum)

power = 300
vel = np.linspace(0.1, 5, 10)
design = designs.ConstantPower(power, geom, vel, bend=True, rpm0=300)

rpm = 300
# design = designs.ConstantRPM(rpm, geom, vel, bend=True, fluid=None, name=None)

offsets = np.linspace(-8, 8, 3)
# design = designs.VariablePitch(power, offsets, geom, vel, bend=True)

# design.eval_performance(verbose=True)
design.compile_data()

sub = {
    'mass': 400.2,
    'frontal_area': 0.2636,
    'drag_coef': 0.04
}

initial_gate = 42
final_gate = 52

design.calc_speed(sub)


design.plot_aero('thrust', 'torque', 'efficiency', save=True)
design.plot_struct('von_misses', save=True)
design.plot_race(initial_gate, final_gate, save=True)
