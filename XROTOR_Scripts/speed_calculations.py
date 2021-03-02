import os
import scipy.integrate
import numpy as np
import matplotlib.pyplot as plt


class RaceSpeed:
    def __init__(self, design, drag_coef, frontal_area, sub_mass):
        self.num_refined = 500
        self.write_file = design.folder.speed_file
        self.plot_file = os.path.join(design.folder.aero_plots, 'displacement.png')
        self.vel_list = design.vel_list
        self.vel_refined = np.zeros(self.num_refined)
        self.max_speed = np.NaN
        self.initial_gate = 0
        self.final_gate = 0

        self.displacement, self.ideal_displacement = self.calc_speed(design, drag_coef, frontal_area, sub_mass)

    def find_recorded_speed(self, initial_gate, final_gate, write=False):
        self.initial_gate = initial_gate
        self.final_gate = final_gate
        initial_vel = linearly_interp(self.displacement, mps_to_knot(self.vel_refined), initial_gate)
        final_vel = linearly_interp(self.displacement, mps_to_knot(self.vel_refined), final_gate)
        self.max_speed = (initial_vel + final_vel) / 2
        if write:
            self._write_max_speed()

    def _write_max_speed(self):
        with open(self.write_file, 'w') as f:
            speed = mps_to_knot(self.max_speed)
            f.write(f'The Recorded Speed is: {speed}')

    def plot(self, save=False, disp=False):
        plt.figure()
        plt.title('Speed Along Racetrack')
        plt.xlabel('Displacement [m]')
        plt.ylabel('Speed [knots]')
        plt.xlim([0, 1.1*self.final_gate])
        plt.grid()

        plt.plot(self.displacement, mps_to_knot(self.vel_refined), label='actual')
        plt.plot(self.ideal_displacement, mps_to_knot(self.vel_refined), label='100% efficiency')

        if not np.isnan(self.max_speed):
            top = max(mps_to_knot(self.vel_refined))
            bottom = min(mps_to_knot(self.vel_refined))
            plt.plot([self.initial_gate, self.initial_gate], [top, bottom], '--', label='first gate')
            plt.plot([self.final_gate, self.final_gate], [top, bottom], '--', label='second gate')

        plt.legend()
        if save:
            plt.savefig(self.plot_file)
        if disp:
            plt.show()
        else:
            plt.close()

    def calc_speed(self, design, drag_coef, frontal_area, sub_mass):
        numerator = (sub_mass * design.vel_list)
        drag = design.fluid['density'] * frontal_area * design.vel_list**2 * drag_coef
        denominator = design.thrust_list - drag
        integrand = numerator / denominator
        negative_indices = integrand < 0
        # integrand[negative_indices] = np.nan
        integrand[negative_indices] = np.NaN

        self.vel_refined = np.linspace(min(design.vel_list), max(design.vel_list), self.num_refined)
        yy = np.interp(self.vel_refined, design.vel_list, integrand)

        x = np.zeros(self.num_refined)
        x[0] = 0
        x[1:] = scipy.integrate.cumtrapz(yy, self.vel_refined)

        x_ideal = self._calc_ideal_speed(design, drag_coef, frontal_area, sub_mass)

        return x, x_ideal

    def _calc_ideal_speed(self, design, drag_coef, frontal_area, sub_mass):
        pwr = design.power
        thrust = pwr / self.vel_list
        drag = design.fluid['density'] * frontal_area * design.vel_list ** 2 * drag_coef
        numerator = (sub_mass * design.vel_list)
        denominator = thrust - drag
        integrand = numerator / denominator
        negative_indices = integrand < 0
        integrand[negative_indices] = np.NaN
        self.vel_refined = np.linspace(min(design.vel_list), max(design.vel_list), self.num_refined)
        yy = np.interp(self.vel_refined, design.vel_list, integrand)

        x = np.zeros(self.num_refined)
        x[0] = 0
        x[1:] = scipy.integrate.cumtrapz(yy, self.vel_refined)
        return x


def linearly_interp(x_list, y_list, x_value):
    front_ind = False
    for i, val in enumerate(x_list):
        if x_value < val:
            front_ind = i
            break
    if not front_ind:
        return np.NaN

    back_ind = front_ind-1
    x_2 = x_list[front_ind]
    x_1 = x_list[back_ind]
    y_2 = y_list[front_ind]
    y_1 = y_list[back_ind]

    slope = (y_2-y_1) / (x_2-x_1)
    y_value = y_1 + slope * (x_value-x_1)
    return y_value


def mps_to_knot(velocity):
    return 1.94384*velocity


def first_true(bool_vector):
    for i, bool in enumerate(bool_vector):
        if bool:
            return i
    return None
