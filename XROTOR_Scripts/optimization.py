import designs
import random
import numpy as np
import make_prop

# initialize the population
def init_population(num_sections, initial_geom):



# run multiple generations



# evaluate parent generation
def single_loop(parents, eval_function):
    # constants
    percent_children = 80

    # evaluate parents performance
    map(eval_function, parents)

    # create an empty list for the next generation
    children = []

    # copy over top performer
    fitness = [individual['cost'] for individual in parents]
    children.append(parents[fitness.index(max(fitness))])

    # decide the number of children to have
    num_children = np.floor(percent_children * len(parents))
    # average probability of replication
    CXPB = 0.5 / len(parents)

    # create the combinations to have children
    couple = []
    while len(children) < num_children:
        mean_fitness = np.nanmean(fitness)
        std_fitness = np.nanstd(fitness)

        for individual in parents:
            if not np.isnan(individual['cost']):
                scaling_factor = 1 + (individual['cost'] - mean_fitness) / std_fitness
                if random.random() < CXPB*scaling_factor:
                    couple.append(individual)
                    if len(couple) == 2:
                        children.append(make_child(couple[0], couple[1]))
                        couple = []
                        if not len(children) < num_children:
                            break

    # creating mutations
    MUTPB = 0.2 / (len(parents))
    while len(children) < num_children:
        for individual in parents:
            if random.random < MUTPB:
                children.append(mutate(individual))
                if not len(children) < num_children:
                    break

    return children


def make_child(parent1, parent2):
    random_factor = 1
    child = {
        'hub_diam': parent1['hub_diam'],
        'diam': None,
        'r_over_r': [],
        'c_over_r': [],
        'beta': [],
        'airfoils': [],
        'cost': None
    }

    if len(parent1['r_over_r']) != len(parent2['r_over_r']):
        raise Exception("lists aren't the same size")

    # dealing with the diameter
    mean = (parent1['diam']+parent2['diam']) / 2
    dif = abs(parent1['diam']-parent2['diam']) / 2
    value = random.gauss(mean, dif*random_factor)
    if value > parent1['hub_diam']:
        value = 1.1*parent1['hub_diam']
    child['diam'] = value

    # creating r_over_r spacing
    init_radial = 1.05*child['hub_diam']/child['diam']
    num_sections = len(parent1['r_over_r'])
    child['r_over_r'] = np.linspace(init_radial, 1, num_sections, endpoint=True)

    # dealing with the chord
    for chord1, chord2 in zip(parent1, parent2):
        mean = (chord1+chord2) / 2
        dif = abs(chord1-chord2) / 2
        value = random.gauss(mean, dif*random_factor)
        if value < 0:
            value = 0.001
        child['c_over_r'].append(value)

    # dealing with the angles
    for beta1, beta2 in zip(parent1, parent2):
        mean = (beta1+beta2) / 2
        dif = abs(beta1-beta2) / 2
        value = random.gauss(mean, dif*random_factor)
        if value > 90:
            value = 90
        if value < 0:
            value = 0
        child['beta'].append(value)

    # dealing with foils
    for foil1, foil2 in zip(parent1, parent2):
        if random.random() < 0.5:
            child['airfoils'].append(foil1)
        else:
            child['airfoils'].append(foil2)
    return child


def mutate(parent, possible_foils):
    child = {
        'hub_diam': parent['hub_diam'],
        'diam': None,
        'c_over_r': [],
        'beta': [],
        'airfoils': [],
        'cost': None
    }

    value = random.gauss(parent['diam'], parent['diam']*0.2)
    if value > parent['hub_diam']:
        value = 1.1*parent['hub_diam']
    child['diam'] = value

    # creating r_over_r spacing
    init_radial = 1.05*child['hub_diam']/child['diam']
    num_sections = len(parent['r_over_r'])
    child['r_over_r'] = np.linspace(init_radial, 1, num_sections, endpoint=True)

    # dealing with the chord
    for chord in parent['c_over_r']:
        value = random.gauss(chord, chord*0.2)
        if value < 0.001:
            value = 0.001
        child['c_over_r'].append(value)

    # dealing with beta
    for beta in parent['beta']:
        value = random.gauss(beta, beta*0.2)
        if value > 90:
            value = 90
        if value < 0:
            value = 0
        child['beta'].append(value)

    # dealing with airfoils
    for foil in parent['airfoils']:
        if random.random() < 0.5:
            child['beta'].append(foil)
        else:
            rand_int = random.randint(0, len(possible_foils))
            child['airfoils'].append(possible_foils[rand_int])


# diam: float representing the diameter of rotor
# airfoil: list of numbers corresponding to each arifoil option
# c_over_r: list of floats corresponding to section size
# beta: angle at each radial section
def make_func(speed, power, fluid, material, stress_max):
    def func(individual):
        geom = make_prop.PropGeom()
        geom.diam = individual['diam']
        geom.hub_diam = individual['hub_diam']
        geom.r_over_r = individual['r_over_r']
        geom.c_over_r = individual['c_over_r']
        geom.beta = individual['beta']
        geom.airfoils = individual['airfoil']
        
        geom.init_aero()
        geom.init_structural(material)
        
        design = designs.ConstantPower(geom, power, [0.1, speed], 'out\\ConstPwr', [True, False], fluid, rpm0=300)
        
        design.evaluate_aero()
        design.compile_data()
        design.eval_structural()
        
        if design.von_misses[0] > stress_max:
            return np.NaN
        else:
            return design.thrust[1]
    return func

