import os


def run_animation():
    from time import sleep
    for i in range(10):
        print('.', end='')
        sleep(0.25)
    print('.', end='\r')


class XRotorInterface:
    def __init__(self, verbose=False):
        self.xrotor_path = 'bin\\xrotor.exe'
        self.verbose = verbose
        print('attempting to spawn XROTOR instance from ' + self.xrotor_path)
        self._create_process()

    def __call__(self, command):
        if self.verbose:
            print('sending command: ' + str(command))
        self._send_command(command)

    def finalize(self):
        print('finalizing xrotor interface')
        self._kill_process()

    def _create_process(self):
        raise NotImplementedError

    def _send_command(self, command):
        raise NotImplementedError

    def _kill_process(self):
        raise NotImplementedError


class XRotorSubprocessInterface(XRotorInterface):
    def _create_process(self):
        from subprocess import Popen, PIPE
        self.process = Popen(self.xrotor_path, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding='utf-8')

    def _send_command(self, command):
        self.process.stdin.write(f'{command}\n')

    def _kill_process(self):
        # the use of threading is because subprocess executes within
        # communicate. it does not spawn multiple threads, simply uses thread
        # functions to determine the execution status of communicate.
        from threading import Thread
        thread = Thread(target=self.process.communicate)
        thread.start()
        while thread.is_alive():
            run_animation()
        print('\n')


# sets all the initial information needed for running XROTOR. This includes fluid properties, propeller geometry,
# aerodynamic properties, and solver type
def initialize_xrotor(geom, vel, rpm, solver, fluid, verbose):
    # object for interfacing with XROTOR
    xr = XRotorSubprocessInterface(verbose)

    # sets the fluid properties
    xr(f"DENS {fluid['density']}")
    xr(f"VISC {fluid['kinematic_viscosity']*fluid['density']}")
    xr(f"VSOU {fluid['speed_sound']}")

    set_geom(xr, geom)          # sets the shape of the blade
    # sets the reynolds number at each radial section
    geom.set_aero(vel, rpm, fluid['kinematic_viscosity'], fluid['speed_sound'])

    init_foils(xr, geom)
    set_foils(xr, geom)             # sets the each foils aerodynamic coefficients

    # Setting solver formulation
    xr("OPER")  # enter operation menu

    xr("FORM")  # enter formulations menu
    xr(solver)  # set the formulation type
    xr('')

    xr('ITER')
    xr('120')

    xr("VELO")  # set forward velocity
    xr(vel)

    return xr


# Sets the shape of the propeller
def set_geom(xr, geom):
    # geom.error_check()
    xr("ARBI")                             # do arbitrary propeller geometry
    xr(geom.blades)                        # set the number of blades
    xr(0)                                  # set flight speed to 0
    xr(geom.diam / 2)                      # set tip radius
    xr(geom.hub_diam / 2)                       # set hub radius
    xr(len(geom.sections))                       # set number of radial sections
    for _, row in geom.sections.iterrows():        # set each of the radial sections r/R, c/R, and angle
        xr(f"{row['rad_ratio']} {row['chord_ratio']} {row['pitch']}")
    xr('n')                                # say no to "Any corrections


# creates the right amount of foils in aero
def init_foils(xr, geom):
    xr('AERO')
    xr('NEW')
    xr(geom.sections.loc[0, 'rad_ratio'])
    for _, row in geom.sections.iterrows():
        xr('NEW')
        xr('1')
        xr(row['rad_ratio'])
    xr('del 1')
    xr('y')
    xr('del 2')
    xr('y')
    xr("")


# sets the aerodynamic properties for each airfoil section
def set_foils(xr, geom):
    xr("AERO")                         # go to airfoil section
    for i, row in geom.curr_aero.iterrows():       # Sets characteristics at each section
        xr(f"EDIT {i + 1}")            # open edit menu for the airfoil

        xr("LIFT")                     # do the lift parameters
        xr(row['zero_lift'])      # zeros-lift alpha (deg)
        xr(row['dcl_da'])      # d(CL)/d(alpha) (/rad)
        xr(row['dcl_da_stall'])      # d(CL)/d(alpha) at stall (/rad)
        xr(row['cl_max'])      # maximum CL
        xr(row['cl_min'])      # minimum CL
        xr(row['dcl'])      # cl increment to stall
        xr(row['cm'])      # cm

        xr("DRAG")                     # do drag parameters
        xr(row['cd_min'])      # minimum cd
        xr(row['cl_cd_min'])      # CL @ min CD
        xr(row['cd2'])     # d(Cd)/d(CL**2)
        xr(row['ref_re'])      # reference Re number
        xr(row['r'])     # Re scaling exponent
        xr(0.8)                          # Mcrit

        xr("")                 # exit edit to aero
    xr("")


def run(geom, vel, rpm, solver, aero_file, fluid, pwr=None, bend_geom=None, bend_file=None, verbose=False):
    overwrite(aero_file)
    xr = initialize_xrotor(geom, vel, rpm, solver, fluid, verbose)

    xr("RPM")          # set RPM
    xr(rpm)

    if pwr is not None:
        xr("POWE")  # set RPM
        xr(pwr)
        xr("P")

    xr("WRIT")         # write to file
    xr(aero_file)
    xr("")             # exit to main menu

    if bend_file is not None:
        xr("BEND")
        xr(f"READ {bend_geom}")
        xr("EVAL")
        xr(f"WRIT {bend_file}")
        xr("")

    xr.finalize()


def overwrite(file):
    if os.path.isfile(file):
        os.remove(file)
