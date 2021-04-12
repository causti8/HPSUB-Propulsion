import matplotlib.pyplot as plt
import numpy as np


def single_plot(design, name):
    if name == 'thrust':
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Thrust [N]')
        plt.title('Thrust vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(design.vel_list), nullify_negatives(design.thrust_list), label='actual')
        plt.plot(mps_to_knot(design.vel_list), nullify_negatives(design.power*design.efficiency_ideal/design.vel_list),
                 label='ideal')
        plt.plot(mps_to_knot(design.vel_list), nullify_negatives(design.power/design.vel_list), label='100% efficient')
        plt.legend()
        plt.ylim([0, 1.1*np.nanmax(design.thrust_list)])

    if name == 'torque':
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Torque [N-m]')
        plt.title('Torque vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(design.vel_list),
                 nullify_negatives(design.torque_list)
                 )

    if name == 'efficiency':
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('Efficiency')
        plt.title('Efficiency vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(design.vel_list), nullify_efficiency(design.efficiency_list), label='Efficiency')
        plt.plot(mps_to_knot(design.vel_list), nullify_negatives(design.efficiency_ideal), label='Ideal Efficiency')
        plt.legend()

    if name == 'RPM':
        plt.figure()
        plt.xlabel('Velocity [Knots]')
        plt.ylabel('RPM')
        plt.title('RPM vs Velocity')
        plt.grid()

        plt.plot(mps_to_knot(design.vel_list),
                 design.rpm_list
                 )

    if name == 'coefficients':
        plt.figure()
        plt.xlabel('Advance Ratio J')
        plt.title('Coefficients Plot')
        plt.grid()

        plt.plot(design.advance_ratio,
                 nullify_efficiency(design.efficiency_list),
                 label=r'$\eta$',
                 )
        plt.plot(design.advance_ratio,
                 nullify_negatives(design.thrust_coef),
                 label=r'$C_t$')
        plt.plot(design.advance_ratio,
                 10 * nullify_negatives(design.torque_coef),
                 label=r'$10 \times C_q$')
        plt.legend()

    if name == 'displacement':
        plt.xlabel('Displacement [m]')
        plt.ylabel('Velocity [Knots]')
        plt.title('Velocity vs Displacement')
        plt.grid()

        plt.plot(design.displacement, mps_to_knot(design.vel_list))


def single_struct_plot(design, name):
    if name == 'von_misses':
        plt.figure()
        plt.title('Blade Stress')
        plt.ylabel('stress [MPa]')
        plt.xlabel('radial location (r/R)')
        for i in range(len(design.vel_list)):
            if design.bend_data[i] is not None:
                plt.plot(design.bend_data[i].data_top['r_over_r'], design.bend_data[i].von_misses / 10 ** 6,
                         label=f'vel = {design.vel_list[i]:.2f}')
        plt.legend()
        plt.grid()


def vpp_plot(variable_pitch, name):
    if name == 'thrust':
        plt.figure()
        plt.title('Thrust vs Velocity')
        plt.ylabel('Thrust [N]')
        plt.xlabel('Velocity [knots]')
        for i, constant_pitch in enumerate(variable_pitch.constant_propellers):
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     constant_pitch.thrust_list,
                     '--', label=f'{variable_pitch.offset_list[i]:.2f}'
                     )
        plt.plot(mps_to_knot(variable_pitch.vel_list),
                 variable_pitch.thrust_list,
                 label='VPP Performance')
        plt.legend()
        plt.grid()

    if name == 'torque':
        plt.figure()
        plt.title('Torque vs Velocity')
        plt.ylabel('Torque [N-m]')
        plt.xlabel('Velocity [knots]')
        for i, constant_pitch in enumerate(variable_pitch.constant_propellers):
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     constant_pitch.torque_list,
                     '--', label=f'{variable_pitch.offset_list[i]:.2f}'
                     )
        plt.plot(mps_to_knot(variable_pitch.vel_list),
                 variable_pitch.torque_list,
                 label='VPP Performance')
        plt.legend()

    if name == 'efficiency':
        plt.figure()
        plt.title('Efficiency vs Velocity')
        plt.ylabel('Efficiency')
        plt.xlabel('Velocity [knots]')
        for i, constant_pitch in enumerate(variable_pitch.constant_propellers):
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     constant_pitch.efficiency_list,
                     '--', label=f'{variable_pitch.offset_list[i]:.2f}'
                     )
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     variable_pitch.efficiency_list,
                     label='VPP Performance')
        plt.legend()

    if name == 'RPM':
        plt.figure()
        plt.title('RPM vs Velocity')
        plt.ylabel('RPM')
        plt.xlabel('Velocity [knots]')
        for i, constant_pitch in enumerate(variable_pitch.constant_propellers):
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     constant_pitch.rpm_list,
                     '--', label=f'{variable_pitch.offset_list[i]:.2f}'
                     )
            plt.plot(mps_to_knot(variable_pitch.vel_list),
                     variable_pitch.rpm_list,
                     label='VPP Performance')
        plt.legend()

    if name == 'coefficients':
        plt.figure()
        plt.xlabel('Advance Ratio J')
        plt.title('Coefficients Plot')
        plt.grid()

        plt.plot(variable_pitch.advance_ratio,
                 nullify_efficiency(variable_pitch.efficiency_list),
                 label=r'$\eta$',
                 )
        plt.plot(variable_pitch.advance_ratio,
                 nullify_negatives(variable_pitch.thrust_coef),
                 label=r'$C_t$')
        plt.plot(variable_pitch.advance_ratio,
                 10 * nullify_negatives(variable_pitch.torque_coef),
                 label=r'$10 \times C_q$')
        plt.legend()


def nullify_negatives(vector):
    new_vector = np.copy(vector)
    for i in range(len(vector)):
        if not np.isnan(vector[i]):
            if vector[i] < 0:
                new_vector[i] = np.NaN
    return new_vector


def nullify_efficiency(vector):
    new_vector = np.copy(vector)
    for i in range(len(vector)):
        if not np.isnan(vector[i]):
            if vector[i] > 1:
                new_vector[i] = np.NaN
            elif vector[i] < 0:
                new_vector[i] = np.NaN
    return new_vector


def mps_to_knot(velocity):
    return 1.94384 * velocity
