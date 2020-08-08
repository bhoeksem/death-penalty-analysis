import random
import json


#random.seed(123)

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

    print(sample_demographics)
    num_picks = sum(list(sample_demographics.values()))
    print(num_picks)

    group_order = []
    denominators = []
    for group in pop:
        group_order.append(group)
        denominators.append(pop[group])

        if group not in sample_demographics:
            sample_demographics[group] = 0

    sum_denominators = sum(denominators)

    print(group_order)
    print(denominators)

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


    print(num_as_bad_as_reality)
    print(num_as_good_as_reality)

    chance_this_bad_or_worse = {}
    for i in range(len(group_order)):
        # Sames are counted twice
        percentile = num_as_bad_as_reality[i] / (num_as_bad_as_reality[i] + num_as_good_as_reality[i])
        chance_this_bad_or_worse[group_order[i]] = percentile

    print(chance_this_bad_or_worse)

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
        'Two Or More Races': '', # NOTE throwing out for now because I don't know what's most fair to do with it
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


#print(inmates)
#print(executions)
#print(year2state2pop)

run_simulations(2008, state2pop["Kentucky"], inmates["Kentucky"])

"""
year2state2chances = {}
for pop_year, state2pop in year2state2pop.items():
    print(pop_year)
    year2state2chances[pop_year] = {}
    for state in state2pop:
        year2state2chances[pop_year][state] = {}
        print()
        print(state)
        if state in inmates:
            year2state2chances[pop_year][state]['inmates'] = run_simulations(pop_year, state2pop[state], inmates[state])
        if state in executions:
            year2state2chances[pop_year][state]['executions'] = run_simulations(pop_year, state2pop[state], executions[state])
    

# TODO
with open("year2state2chances.json", 'w') as f:
    json.dump(year2state2chances, f)
"""




"""

# Alabama
buckets = {
        'white': 3115600.0,
        'black': 1257300.0,
        'hispanic': 204800.0,
        'other': 92100.0,
        'asian': 63800.0,
        'aian': 19000.0
    }
num_picks = 175
target_bucket = 'black'
threshold = 89

"""
buckets = {
        'white': 5358000.0,
        'black': 3158000.0,
        'hispanic': 994300.0,
        'other': 265000.0,
        'asian': 421200.0,
        'aian': 16300.0
    }
num_picks = 76
target_bucket = 'black'
threshold = 28
"""

sum_buckets = 0
for bucket in buckets:
    sum_buckets += buckets[bucket]

bucket_list = []
cumulative_prob_list = []

cumulative_prob = 0
for bucket in buckets:
    cumulative_prob += (buckets[bucket] / sum_buckets)

    bucket_list.append(bucket)
    cumulative_prob_list.append(cumulative_prob)

print(bucket_list)
print(cumulative_prob_list)

num_crazier = 0
num_sims = 1000000

for k in range(num_sims):
    if k > 0 and k % 10000 == 0:
        print((1.0 * num_crazier) / k)
    picks = {}
    for i in range(num_picks):
        prob = random.random()
        for j in range(len(bucket_list)):
            if prob <= cumulative_prob_list[j]:
                bucket = bucket_list[j]
                if bucket not in picks:
                    picks[bucket] = 0
                picks[bucket] += 1
                break
    if picks[target_bucket] >= threshold:
        num_crazier += 1


print(num_crazier)


"""
