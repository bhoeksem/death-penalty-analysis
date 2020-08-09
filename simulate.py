#!/usr/bin/python3

import random
import json


def cumulative_from_denominators(picks, denominators, sum_denominators):
    cumulative_prob_list = []

    cumulative_prob = 0
    for i in range(len(denominators)):
        cumulative_prob += ((denominators[i] - picks[i]) / sum_denominators)
        cumulative_prob_list.append(cumulative_prob)

    return cumulative_prob_list


def run_simulation(num_picks, sum_denominators, denominators):
    picks = [0 for _ in denominators]

    for i in range(num_picks):
        cumulative_prob_list = cumulative_from_denominators(picks, denominators, sum_denominators-i)
        prob = random.random()
        for j in range(len(denominators)):
            if prob <= cumulative_prob_list[j]:
                picks[j] += 1
                break

    return picks


def run_simulations(pop_year, pop, sample_demographics):
    num_sims = 100000

    num_picks = sum(list(sample_demographics.values()))

    group_order = []
    denominators = []
    for group in pop:
        group_order.append(group)
        denominators.append(pop[group])

        if group not in sample_demographics:
            sample_demographics[group] = 0

    sum_denominators = sum(denominators)


    sim_picks = []
    for i in range(num_sims):
        sim_picks.append(run_simulation(num_picks, sum_denominators, denominators))

    num_as_bad_as_reality   = [0 for _ in group_order]
    num_as_good_as_reality = [0 for _ in group_order]
    for picks in sim_picks:
        for i in range(len(picks)):
            group = group_order[i]
            if picks[i] >= sample_demographics[group]:
                num_as_bad_as_reality[i] += 1
            if picks[i] <= sample_demographics[group]:
                num_as_good_as_reality[i] += 1


    chance_this_bad_or_worse = {}
    for i in range(len(group_order)):
        # Sames are counted twice
        percentile = num_as_bad_as_reality[i] / (num_as_bad_as_reality[i] + num_as_good_as_reality[i])
        chance_this_bad_or_worse[group_order[i]] = percentile


    return chance_this_bad_or_worse



key_consolidation = {
        'White': 'white',
        'Black': 'black',
        'Hispanic': 'hispanic',
        'Latino': 'hispanic',
        'Latina': 'hispanic',
        'Latino/a': 'hispanic',
        'Asian': 'asian',
        'American Indian or Alaska Native': 'amInd',
        'American Indian/Alaska Native': 'amInd',
        'Native American': 'amInd',
        'Other': 'other',
        'Other Race': 'other',
        'Native Hawaiian/Other Pacific Islander': 'other',
        'Unknown': 'other',

        # Throw out
        'Location': '',
        'State': '',
        'Total': '',
        }

with open('demographics.json') as f:
    demographics = json.load(f)

    year2state2pop = {}

    for year in demographics:
        year2state2pop[year] = {}
        for state in demographics[year]:
            state_name = state['Location']
            for key in list(state.keys()):
                value = state[key]
                consolid_key = key_consolidation[key]
                if consolid_key != '':
                    state[consolid_key] = float(value)
                del state[key]
            year2state2pop[year][state_name] = state

with open('inmates.json') as f:
    inmates_json = json.load(f)
    inmates = {row['State'] : row for row in inmates_json}

    for state in inmates:
        for key in list(inmates[state].keys()):
            value = inmates[state][key]
            consolid_key = key_consolidation[key]
            if consolid_key != '':
                inmates[state][consolid_key] = value
            del inmates[state][key]

with open('executions.json') as f:
    executions_json = json.load(f)

    executions = {}
    for row in executions_json:
        state = row['State*']

        if state not in executions:
            executions[state] = {}

        race = key_consolidation[row['Race']]
        if race not in executions[state]:
            executions[state][race] = 0

        executions[state][race] += 1


year2state2chances = {}
for pop_year, state2pop in year2state2pop.items():
    year2state2chances[pop_year] = {}
    for state in state2pop:
        year2state2chances[pop_year][state] = {}
        if state in inmates:
            year2state2chances[pop_year][state]['inmates'] = run_simulations(pop_year, state2pop[state], inmates[state])
        if state in executions:
            year2state2chances[pop_year][state]['executions'] = run_simulations(pop_year, state2pop[state], executions[state])
    

with open("year2state2chances.json", 'w') as f:
    json.dump(year2state2chances, f)
