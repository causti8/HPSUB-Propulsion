import numpy as np
import matplotlib.pyplot as plt
import functions


def plot_graphs(folder, alpha, cl_actual, cd_actual, cm_actual, data):
    functions.overwrite_path(folder.re_folder())
    plot_cl(folder, alpha, cl_actual, data)

    plot_cd(folder, cl_actual, cd_actual, data)

    plot_cm(folder, alpha, cm_actual, data)


def plot_cl(folder, alpha, cl_actual, data):
    minimum_alpha = (data['minimum Cl'] / data['d(Cl)/d(alpha)']) + deg_to_rad(data['zero-lift angle(deg)'])
    maximum_alpha = (data['maximum Cl'] / data['d(Cl)/d(alpha)']) + deg_to_rad(data['zero-lift angle(deg)'])
    stall_alpha = data['Cl increment to stall'] / data['d(Cl)/d(alpha) @stall'] + maximum_alpha

    minimum_alpha = rad_to_deg(minimum_alpha)
    maximum_alpha = rad_to_deg(maximum_alpha)
    stall_alpha = rad_to_deg(stall_alpha)

    plt.figure()
    plt.title('X-Foil Lift Coefficient Fit')
    plt.xlabel('Angle of Attack ($alpha$) [deg]')
    plt.ylabel('Lift Coefficient (CL)')

    plt.plot([minimum_alpha, maximum_alpha], [data['minimum Cl'], data['maximum Cl']], label='main linear fit')
    plt.plot([maximum_alpha, stall_alpha],
             [data['maximum Cl'], data['maximum Cl'] + data['Cl increment to stall']],
             label='stall linear fit'
             )
    plt.plot(rad_to_deg(alpha), cl_actual, label='XFoil Data')

    plt.legend()
    plt.grid()
    plt.savefig(folder.cl_plot())
    plt.close()


def plot_cd(folder, cl_actual, cd_actual, data):

    plt.figure()
    plt.title('X-Foil Drag Coefficient Parabolic Fit')
    plt.xlabel('Coefficient of Lift (Cl)')
    plt.ylabel('Coefficient of drag (Cd)')

    cd_predicted = data['(1/2)d^2(Cd)/d^2(Cl)'] * (cl_actual - data['Cl at minimum Cd'])**2 + data['minimum Cd']

    plt.plot(cl_actual, cd_actual, label='XFoil Data')
    plt.plot(cl_actual, cd_predicted, label='Parabolic Fit')

    plt.plot([data['minimum Cl'], data['minimum Cl']],
             [min(cd_actual), max(cd_actual)], '--', label='minimum Cl'
             )
    plt.plot([data['maximum Cl'], data['maximum Cl']],
             [min(cd_actual), max(cd_actual)], '--', label='maximum Cl'
             )
    plt.plot([data['maximum Cl']+data['Cl increment to stall'], data['maximum Cl']+data['Cl increment to stall']],
             [min(cd_actual), max(cd_actual)], '--', label='Increment to Stall'
             )

    plt.legend()
    plt.grid()
    plt.savefig(folder.cd_plot())
    plt.close()


def plot_cm(folder, alpha, cm_actual, data):
    plt.figure()
    plt.title('X-Foil Moment Coefficient Constant Fit')
    plt.xlabel('Angle of Attack ($alpha$) [deg]')
    plt.ylabel('Moment Coefficient (Cm)')

    plt.plot(deg_to_rad(alpha), cm_actual, label='XFoil Data')
    plt.plot([min(deg_to_rad(alpha)), max(deg_to_rad(alpha))], [data['Cm'], data['Cm']], label='Constant Fit')

    plt.grid()
    plt.savefig(folder.cm_plot())
    plt.close()


def deg_to_rad(value):
    return (np.pi / 180) * value


def rad_to_deg(value):
    return (180 / np.pi) * value
