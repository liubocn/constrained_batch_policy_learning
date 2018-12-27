"""
Created on December 12, 2018

@author: clvoloshin, 
"""
from fitted_algo import FittedAlgo
import numpy as np
from tqdm import tqdm
from env_nn import *

class LakeFittedQEvaluation(FittedAlgo):
    def __init__(self, initial_states, num_inputs, grid_shape, dim_of_actions, max_epochs, gamma,model_type='mlp', position_of_goals=None, position_of_holes=None, num_frame_stack=None):

        '''
        An implementation of fitted Q iteration

        num_inputs: number of inputs
        dim_of_actions: dimension of action space
        max_epochs: positive int, specifies how many iterations to run the algorithm
        gamma: discount factor
        '''
        self.model_type = model_type
        self.initial_states = initial_states
        self.num_inputs = num_inputs
        self.dim_of_actions = dim_of_actions
        self.max_epochs = max_epochs
        self.gamma = gamma
        self.grid_shape = grid_shape
        self.position_of_holes = position_of_holes
        self.position_of_goals = position_of_goals
        self.num_frame_stack = num_frame_stack

        super(LakeFittedQEvaluation, self).__init__()

    def run(self, policy, which_cost, dataset, epochs=500, epsilon=1e-8, desc='FQE', g_idx=None, **kw):
        # dataset is the original dataset generated by pi_{old} to which we will find
        # an approximately optimal Q

        self.Q_k = self.init_Q(model_type=self.model_type, position_of_holes=self.position_of_holes, position_of_goals=self.position_of_goals, num_frame_stack=self.num_frame_stack, **kw)

        X_a = np.hstack(dataset.get_state_action_pairs())
        x_prime = dataset['x_prime']

        index_of_skim = self.skim(X_a, x_prime)
        X_a = X_a[index_of_skim]
        x_prime = x_prime[index_of_skim][:,0]
        dataset.set_cost(which_cost, idx=g_idx)
        dataset_costs = dataset['cost'][index_of_skim]
        dones = dataset['done'][index_of_skim]

        for k in tqdm(range(self.max_epochs), desc=desc):

            # {((x,a), r+gamma* Q(x',pi(x')))}
            
            # if k == 0:
            #     # Q_0 = 0 everywhere
            #     costs = dataset_costs
            # else:
            costs = dataset_costs + (self.gamma*self.Q_k(x_prime, policy(x_prime)).reshape(-1)*(1-dones.astype(int))).reshape(-1)

            self.fit(X_a, costs, epochs=epochs, batch_size=X_a.shape[0], epsilon=epsilon, evaluate=False, verbose=0)

            # if not self.Q_k.callbacks_list[0].converged:
            #     print 'Continuing training due to lack of convergence'
            #     self.fit(X_a, costs, epochs=epochs, batch_size=X_a.shape[0], epsilon=epsilon, evaluate=False, verbose=0)


        return np.mean([self.Q_k(state, policy(state)) for state in self.initial_states])

    def init_Q(self, epsilon=1e-10, **kw):
        return LakeNN(self.num_inputs, 1, self.grid_shape, self.dim_of_actions, self.gamma, epsilon, **kw)

class CarFittedQEvaluation(FittedAlgo):
    def __init__(self, state_space_dim, dim_of_actions, max_epochs, gamma, model_type='cnn', num_frame_stack=None):

        '''
        An implementation of fitted Q iteration

        num_inputs: number of inputs
        dim_of_actions: dimension of action space
        max_epochs: positive int, specifies how many iterations to run the algorithm
        gamma: discount factor
        '''
        self.model_type = model_type


        self.state_space_dim = state_space_dim
        self.dim_of_actions = dim_of_actions
        self.max_epochs = max_epochs
        self.gamma = gamma
        self.num_frame_stack = num_frame_stack

        super(CarFittedQEvaluation, self).__init__()

    def run(self, policy, which_cost, dataset, epochs=1, epsilon=1e-8, desc='FQE', g_idx=None, **kw):
        # dataset is the original dataset generated by pi_{old} to which we will find
        # an approximately optimal Q

        self.Q_k = self.init_Q(model_type=self.model_type, num_frame_stack=self.num_frame_stack, **kw)

        X_a = dataset.get_state_action_pairs()
        x_prime = dataset['x_prime']

        
        
        dataset.set_cost(which_cost, idx=g_idx)
        dataset_costs = dataset['cost']
        dones = dataset['done']

        for k in tqdm(range(self.max_epochs), desc=desc):

            # {((x,a), r+gamma* Q(x',pi(x')))}
            
            # if k == 0:
            #     # Q_0 = 0 everywhere
            #     costs = dataset_costs
            # else:
            costs = dataset_costs + (self.gamma*self.Q_k(x_prime, policy(x_prime)).reshape(-1)*(1-dones.astype(int))).reshape(-1)

            self.fit(X_a, costs, epochs=epochs, batch_size=128, epsilon=epsilon, evaluate=False, verbose=0)

            # if not self.Q_k.callbacks_list[0].converged:
            #     print 'Continuing training due to lack of convergence'
            #     self.fit(X_a, costs, epochs=epochs, batch_size=X_a.shape[0], epsilon=epsilon, evaluate=False, verbose=0)

        initial_states = np.unique([episode['x'][0] for episode in dataset.episodes], axis=0)
        return np.mean(self.Q_k(initial_states, policy(initial_states)))

    def init_Q(self, epsilon=1e-10, **kw):
        return CarNN(self.state_space_dim, self.dim_of_actions, self.gamma, convergence_of_model_epsilon=epsilon, **kw)

