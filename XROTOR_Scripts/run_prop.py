import xrotor
import file_tools


# sets all the initial information needed for running XROTOR. This includes fluid properties, propeller geometry,
# aerodynamic properties, and solver type
def initialize_xrotor(geom, vel, rpm, solver, fluid, verbose):
    # object for interfacing with XROTOR
    xr = xrotor.XRotorSubprocessInterface(verbose)

    # sets the fluid properties
    xr(f"DENS {fluid['density']}")
    xr(f"VISC {fluid['viscosity']*fluid['density']}")
    xr(f"VSOU {fluid['speed_sound']}")

    set_geom(xr, geom)          # sets the shape of the blade
    geom.set_re_blade(vel, rpm, fluid['viscosity'])   # sets the reynolds number at each radial section

    init_foils(xr, geom)
    set_foils(xr, geom)         # sets the each foils aerodynamic coefficients

    # Setting solver formulation
    xr("OPER")  # enter operation menu

    xr("FORM")  # enter formulations menu
    xr(solver)  # set the formulation type
    xr('')

    xr('ITER')
    xr('60')

    xr("VELO")  # set forward velocity
    xr(vel)

    return xr


# Sets the shape of the propeller
def set_geom(xr, geom):
    # check that radial sections are in acceptable location
    if abs(geom.r_over_r[0] - geom.hub_diam/geom.diam) >= 0.01:
        raise Exception("Radial sections must lie between "
                        "%.6f and 1" % (geom.hub_diam / geom.diam))

    xr("ARBI")                             # do arbitrary propeller geometry
    xr(geom.blades)                        # set the number of blades
    xr(0)                                  # set flight speed to 0
    xr(geom.diam / 2)                      # set tip radius
    xr(geom.hub_diam / 2)                       # set hub radius
    xr(geom.num_sections)                       # set number of radial sections
    for i in range(geom.num_sections):        # set each of the radial sections r/R, c/R, and angle
        xr(f"{geom.r_over_r[i]} {geom.c_over_r[i]} {geom.beta[i]}")
    xr('n')                                # say no to "Any corrections


# creates the right amount of foils in aero
def init_foils(xr, prop):
    xr('AERO')
    xr('NEW')
    xr(prop.r_over_r[0])
    for i in range(1, prop.num_sections):
        xr('NEW')
        xr('1')
        xr(prop.r_over_r[i])
    xr('del 1')
    xr('y')


# sets the aerodynamic properties for each airfoil section
def set_foils(xr, geom):
    xr("AERO")                         # go to airfoil section
    for i in range(geom.num_sections):       # Sets characteristics at each section
        xr(f"EDIT {i + 1}")            # open edit menu for the airfoil

        xr("LIFT")                     # do the lift parameters
        xr(geom.foil_aero[i].performance['zero-lift alpha(deg)'])      # zeros-lift alpha (deg)
        xr(geom.foil_aero[i].performance['d(Cl)/d(alpha)'])      # d(CL)/d(alpha) (/rad)
        xr(geom.foil_aero[i].performance['d(Cl)/d(alpha)@Stall'])      # d(CL)/d(alpha) at stall (/rad)
        xr(geom.foil_aero[i].performance['maximum Cl'])      # maximum CL
        xr(geom.foil_aero[i].performance['minimum Cl'])      # minimum CL
        xr(geom.foil_aero[i].performance['Cl increment to stall'])      # cl increment to stall
        xr(geom.foil_aero[i].performance['Cm'])      # cm

        xr("DRAG")                     # do drag parameters
        xr(geom.foil_aero[i].performance['minimum Cd'])      # minimum cd
        xr(geom.foil_aero[i].performance['Cl at minimum Cd'])      # CL @ min CD
        xr(geom.foil_aero[i].performance['d^2(Cd)/d^2(Cl)'])     # d(Cd)/d(CL**2)
        xr(geom.foil_aero[i].performance['reference Re number'])      # reference Re number
        xr(geom.foil_aero[i].performance['Re scaling exponent'])     # Re scaling exponent
        xr(geom.foil_aero[i].performance['critical mach'])                          # Mcrit

        xr("")                 # exit edit to aero
    xr("")


# run at single velocity and either rpm or power
# geom: PropGeom object containing geometry and aerodynamic information
# rpm: rpm of the propeller
# vel: velocity of the propeller
# solver: solver to be used. Options are 'VRTX', 'POT', 'GRAD'
# outfile: file to write data to
# liquid: liquid propeller is in
# pwr: power to run the propeller at
# verbose: True will cause the XROTOR inputs to be output to console
def run(geom, vel, rpm, solver, outfile, fluid, pwr=False, verbose=False):
    file_tools.overwrite(outfile)
    xr = initialize_xrotor(geom, vel, rpm, solver, fluid, verbose)

    if pwr is not False:
        xr("POWE")  # set RPM
        xr(pwr)
        xr("P")
    else:
        xr("RPM")          # set RPM
        xr(rpm)

    xr("WRIT")         # write to file
    xr(outfile)
    xr("")             # exit to main menu
    xr.finalize()


def evaluate_strength(geom, vel, rpm, solver, struct_file, outfile, liquid, verbose, pwr=None):
    file_tools.overwrite(outfile)
    file_tools.overwrite('temp_aero.txt')

    xr = initialize_xrotor(geom, vel, rpm, solver, liquid, verbose)
    if pwr is None:
        xr("RPM")
        xr(rpm)
    if pwr is not None:
        xr("POWE")
        xr(pwr)
        xr("P")
    xr("")

    xr("BEND")
    xr(f"READ {struct_file}")
    xr("EVAL")
    xr(f"WRIT {outfile}")
    xr("")
    xr.finalize()
