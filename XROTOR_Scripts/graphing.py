import matplotlib.pyplot as plt
import numpy as np


def single_plot(name, aero_data):
    if 'thrust' == name:
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Thrust [N]')
        plt.title('Thrust vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(aero_data['vel']), aero_data['thrust'], label='actual')
        plt.plot(mps_to_knot(aero_data['vel']),
                 aero_data['power'] * aero_data['efficiency_ideal'] / aero_data['vel'], label='ideal')
        plt.plot(mps_to_knot(aero_data['vel']), (aero_data['power'] / aero_data['vel']), label='100% efficient')
        plt.legend()
        plt.ylim([0, 1.1 * np.nanmax(aero_data['thrust'])])

    if 'torque' == name:
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Torque [N-m]')
        plt.title('Torque vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(aero_data['vel']), aero_data['torque'])

    if 'efficiency' == name:
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Efficiency')
        plt.title('Efficiency vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(aero_data['vel']), (aero_data['efficiency']), label='Efficiency')
        plt.plot(mps_to_knot(aero_data['vel']), (aero_data['efficiency_ideal']), label='Ideal Efficiency')
        plt.legend()

    if 'RPM' == name:
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('RPM')
        plt.title('RPM vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(aero_data['vel']),
                 aero_data['rpm']
                 )

    if 'coefficients' == name:
        plt.figure()
        plt.xlabel('Advance Ratio J')
        plt.title('Coefficients Plot')
        plt.grid()

        plt.plot(aero_data['advance_ratio'],
                 (aero_data['efficiency']),
                 label=r'$\eta$',
                 )
        plt.plot(aero_data['advance_ratio'],
                 (aero_data['thrust_coef']),
                 label=r'$C_t$')
        plt.plot(aero_data['advance_ratio'],
                 10 * (aero_data['torque_coef']),
                 label=r'$10 \times C_q$')
        plt.legend()

    if 'displacement' == name:
        plt.xlabel('Displacement [m]')
        plt.ylabel('Velocity [Knots]')
        plt.title('Velocity vs Displacement')
        plt.grid()

        plt.plot(aero_data['displacement'], mps_to_knot(aero_data['vel']))


def single_struct_plot(name, bend_data):
    if 'von_misses' == name:
        plt.figure()
        plt.title('Blade Stress')
        plt.ylabel('stress [MPa]')
        plt.xlabel('radial location (r/R)')
        for vel in set(bend_data['vel']):
            data_vel = bend_data[bend_data['vel'] == vel]
            plt.plot(data_vel['r/R'], data_vel['von_misses'] / 10 ** 6, label=f'vel = {mps_to_knot(vel):.2f} [knots]')
        plt.legend()
        plt.grid()


def plot_race(race_data, initial_gate, final_gate):
    plt.figure()
    plt.title('Speed Along Racetrack')
    plt.xlabel('Displacement [m]')
    plt.ylabel('Speed [knots]')
    plt.xlim([0, 1.1*final_gate])
    plt.grid()

    plt.plot(race_data['displacement'], mps_to_knot(race_data['vel']), label='actual')
    # plt.plot(race_data['ideal_displacement'], mps_to_knot(race_data['vel']), label='100% efficiency')

    gate1_speed = mps_to_knot(find_speed(race_data, initial_gate))
    gate2_speed = mps_to_knot(find_speed(race_data, final_gate))
    top_speed = mps_to_knot(race_data.loc[race_data['displacement'].idxmax(), 'vel'])

    if not np.isnan(gate1_speed):
        plt.axvline(initial_gate, ls='--', color='green', label=f'first gate, Vel = {gate1_speed:.2f}')

        if not np.isnan(gate2_speed):
            plt.axvline(final_gate, ls='--', color='red', label=f'second gate, Vel = {gate2_speed:.2f}')

    plt.ylim([0, top_speed*1.1])
    plt.legend()


def vpp_plot(aero, aero_all, name):
    if name == 'thrust':
        plt.figure()
        plt.title('Thrust vs Velocity')
        plt.ylabel('Thrust [N]')
        plt.xlabel('Velocity [knots]')

        for off in set(aero_all['angle_offset']):
            masked = aero_all[aero_all['angle_offset'] == off]
            plt.plot(mps_to_knot(masked['vel']), masked['thrust'], '--', label=f'{off}')
        plt.plot(mps_to_knot(aero['vel']), aero['thrust'], label='VPP Performance')
        plt.legend()
        plt.grid()

    if name == 'torque':
        plt.figure()
        plt.title('Torque vs Velocity')
        plt.ylabel('Torque [N-m]')
        plt.xlabel('Velocity [knots]')
        for off in set(aero_all['angle_offset']):
            masked = aero_all[aero_all['angle_offset'] == off]
            plt.plot(mps_to_knot(masked['vel']), masked['torque'], '--', label=f'{off}')
        plt.plot(mps_to_knot(aero['vel']), aero['torque'], label='VPP Performance')
        plt.legend()
        plt.grid()
        plt.legend()

    if name == 'efficiency':
        for off in set(aero_all['angle_offset']):
            masked = aero_all[aero_all['angle_offset'] == off]
            plt.plot(mps_to_knot(masked['vel']), masked['efficiency'], '--', label=f'{off}')
        plt.plot(mps_to_knot(aero['vel']), aero['efficiency'], label='VPP Performance')

        plt.legend()
        plt.grid()
        plt.legend()

    if name == 'RPM':
        plt.figure()
        plt.title('RPM vs Velocity')
        plt.ylabel('RPM')
        plt.xlabel('Velocity [knots]')
        for off in set(aero_all['angle_offset']):
            masked = aero_all[aero_all['angle_offset'] == off]
            plt.plot(mps_to_knot(masked['vel']), masked['efficiency'], '--', label=f'{off}')
        plt.plot(mps_to_knot(aero['vel']), aero['efficiency'], label='VPP Performance')

        plt.grid()
        plt.legend()
        plt.legend()

    if name == 'coefficients':
        plt.figure()
        plt.xlabel('Advance Ratio J')
        plt.title('Coefficients Plot')

        plt.plot(aero['advance_ratio'], aero['efficiency_list'], label=r'$\eta$')
        plt.plot(aero['advance_ratio'], (aero['thrust_coef']), label=r'$C_t$')
        plt.plot(aero['advance_ratio'], 10 * (aero['torque_coef']), label=r'$10 \times C_q$')

        plt.grid()
        plt.legend()


def find_speed(race_data, location):
    low_ind = race_data[race_data['displacement'] < location]['vel'].idxmax()
    high_ind = race_data[race_data['displacement'] > location]['vel'].idxmin()
    return (race_data.loc[low_ind, 'vel'] + race_data.loc[high_ind, 'vel']) / 2


def mps_to_knot(velocity):
    return 1.94384 * velocity
