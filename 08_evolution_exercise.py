from typing import Callable, Optional
from random import choice, randint, shuffle, choices, random

##################################################
################### STATE TYPE ###################
##################################################

State = list[int] #list of 8 integers

def valid_state(state : State) -> bool:
    return (len(set(state)) == len(state) and
            all(num in range(8) for num in state))

def valid_population(states : list[State]) -> bool:
    return all(valid_state(state) for state in states)

##################################################
########## INITIALIZATION OF POPULATION ##########
##################################################

def random_state() -> State:
    state = list(range(8))
    shuffle(state)
    return state

def random_population(population_size : int) -> list[State]:
    return [ random_state() for _ in range(population_size) ]

def shuffle_population(states : list[State]) -> list[State]:
    shuffled_states = states.copy()
    shuffle(shuffled_states)
    return shuffled_states

##################################################
################ FITNESS FUNCTION ################
##################################################

def fitness(state : State) -> int:
    # can get assertion error
    assert valid_state(state)
    attacks = 0
    for x_a, y_a in enumerate(state):
        for x_b, y_b in enumerate(state):
            if x_b < x_a+1: continue
            attacks += int(x_a+y_a == x_b+y_b) + int(y_a-x_a == y_b-x_b)
    return sum(range(8)) - attacks

def is_solution(state : State) -> bool:
    return fitness(state) == sum(range(8))

def contains_solution(states : list[State]) -> Optional[State]:
    for state in states:
        if is_solution(state):
            return state
    return None

##################################################
############### PRINTING FUNCTIONS ###############
##################################################

def print_state(state : State):
    queens = list(enumerate(state))
    for i in range(8):
        for j in range(8):
            print('|', end='')
            if (i,j) in queens:
                print('Q', end='')
            else:
                print('_', end='')
        print('|')


def print_population(states : list[State], f : Callable[[State],int] = fitness) -> None:
    for state in states:
        assert valid_state(state)
        print(state, '-->', f(state))
    print('#'*31)

##################################################
################### SELECTION ####################
##################################################

def selection(states : list[State], min_val : int, 
                f : Callable[[State],int] = fitness, 
                oversampling : bool = True
             ) -> list[State]:
    preserved_states = [ state for state in states if f(state) > min_val ]
    if oversampling:
        while len(preserved_states) < len(states):
            preserved_states.append(choice(preserved_states))
    return preserved_states


def selection_roulette(states : list[State], 
                        f : Callable[[State],int] = fitness
                      ) -> list[State]:
    preserved_states : list[State] = []
    
    # Idea: Check lecture 7 (evolution) slide 14
    #       Use random.choices (and the weights and k optional argument)
    #           to choose k "good" states randomly
    #       The weights should be the deduced using the fitness function
    fitness_values = [f(state) for state in states]
    
    total_fitness = sum(fitness_values)
    probabilities = [fitness_val / total_fitness for fitness_val in fitness_values]
    k = len(states)
    preserved_states = choices(states, probabilities, k=k)  

    return preserved_states


##################################################
################# RECOMBINATION ##################
##################################################

def recombination(states : list[State]) -> list[State]:
    new_states : list[State] = []
    for i in range(0,len(states)-1,2):
        new_states += recombine(states[i], states[i+1])
    assert valid_population(states)
    return new_states

def recombine(state_a : State, state_b : State) -> tuple[State, State]:
      # Choose 2 random indexes for division barriers
    idx1, idx2 = sorted([randint(0, len(state_a)-1), randint(0, len(state_a)-1)])
    # recombination
    childstate_a = state_a[:idx1] + state_b[idx1:idx2] + state_a[idx2:]
    childstate_b = state_b[:idx1] + state_a[idx1:idx2] + state_b[idx2:]

    return childstate_a, childstate_b

##################################################
##################### REPAIR #####################
##################################################

def repair(states : list[State]) -> list[State]:
    new_states : list[State] = []
    for i in range(0,len(states)-1,2):
        new_states += fix(states[i], states[i+1])
    assert valid_population(new_states)
    return new_states

def fix(state_a : State, state_b : State) -> tuple[State,State]:
    state_a_, state_b_ = state_a.copy(), state_b.copy()
    for element in set(state_a_):
        if state_a_.count(element) > 1:
            # Find a good substitute for the repeated element in state_b_
            try:
                index_to_replace = state_b_.index(element)
            except ValueError:
                # Handle the case when the element doesn't exist in state_b_
                continue

            try:
                substitute = next(num for num in state_b_ if state_b_.count(num) == 0)
            except StopIteration:
                # Handle the case when there are no available substitutes
                substitute = element  # You can choose a different strategy here

            state_b_[index_to_replace] = substitute

    return state_a_, state_b_

##################################################
#################### MUTATION ####################
##################################################

def mutation(states : list[State], chance : float) -> list[State]:
    new_population = [mutate(state, chance) for state in states]
    assert valid_population(new_population)
    return new_population

def mutate(state : State, chance : float) -> State:
    mutated_state : list[State] = state.copy()
    # Idea: Pick 2 random indexes and swap the elements on those positions
    #       Do that only with the given chance! (Suggestion: use random.random())
     # Pick 2 random indexes and swap the elements on those positions with the given chance
    if random.random() < chance:
        idx1, idx2 = randint(0, len(state)-1), randint(0, len(state)-1)
        mutated_state[idx1], mutated_state[idx2] = mutated_state[idx2], mutated_state[idx1]
    return mutated_state

##################################################
################## REPLACEMENT ###################
##################################################

def replacement(original : list[State], evolved : list[State], 
                k : int,
                f : Callable[[State],int] = fitness
             ) -> list[State]:
    return sorted(original,key=f)[k:] + sorted(evolved,key=f)[-k:]

##################################################
################### SIMULATION ###################
##################################################

def simulate(starting_state : list[State], 
             num_cycles : int,
             mutation_prob : float,
             use_roulette : bool,
             min_fitness : Optional[int]) -> None:
    current_state = starting_state.copy()
    for i in range(num_cycles):
        evolved_state = (selection_roulette(current_state)
                         if use_roulette else
                         selection(current_state, min_fitness))
        evolved_state = shuffle_population(evolved_state)
        evolved_state = recombination(evolved_state)
        evolved_state = repair(evolved_state)
        evolved_state = mutation(evolved_state, mutation_prob)
        current_state = replacement(current_state,evolved_state,len(current_state)//2)
        print_population(current_state)
        solution = contains_solution(current_state)
        if solution:
            print(f'solution found after {i+1} steps')
            print_state(solution)
            break
    else:
        print('No solution was found')

def main():
    pop_size = input('Population size:')
    num_iter = input('Number of iterations:')
    mut_prob = input('Mutation probability:')
    roulette = input('Use roulette selection [Y/n]:')
    
    pop_size = int(pop_size)   if pop_size else 4
    num_iter = int(num_iter)   if num_iter else 100
    mut_prob = float(mut_prob) if mut_prob else 0.75
    assert 0 <= mut_prob <= 1
    roulette = True if roulette in ['Y','y',''] else False
    
    if not roulette:
        min_fit = input('Minimum fitness value for selection:')
        min_fit = int(min_fit) if min_fit else 21
    else:
        min_fit = None
    
    simulate(random_population(pop_size),num_iter,mut_prob,roulette,min_fit)

if __name__ == "__main__":
    main()