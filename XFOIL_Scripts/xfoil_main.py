import numpy as np
import functions

# bounds used for curve fitting in degrees
bounds = [-2, 6]
# list of reynolds numbers to evaluate performance at
re_list = np.linspace(1e5, 2e6, 10)

# list of angles to run through XFOIL
alpha = [-8, 14, 0.1]
# Name of the airfoil
airfoil = 'eppler71.txt'

# naca=True means it is a naca airfoil. If False it will look for a coordinate file.
# An example of false is the Clark-Y airfoil
functions.analyze_airfoil(airfoil, fit_bounds=bounds, alpha_range=alpha, re_list=re_list, pane=350, naca=False)
