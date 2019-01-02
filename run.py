"""
Created on December 12, 2018

@author: clvoloshin, 
"""
from pyvirtualdisplay import Display
import numpy as np
np.random.seed(3141592)
import tensorflow as tf
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.Session(config=config)
from optimization_problem import Program
from fittedq import *
from exponentiated_gradient import ExponentiatedGradient
from fitted_off_policy_evaluation import *
from exact_policy_evaluation import ExactPolicyEvaluator
from stochastic_policy import StochasticPolicy
from DQN import DeepQLearning
from print_policy import PrintPolicy
from keras.models import load_model
from keras import backend as K
from env_dqns import *
import deepdish as dd
import time
import os
np.set_printoptions(suppress=True)

def main(env_name, headless):

    if headless:
        display = Display(visible=0, size=(1280, 1024))
        display.start()
    ###
    #paths
    
    model_dir = os.path.join(os.getcwd(), 'models')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    ###

    if env_name == 'lake':
        from config_lake import *
    elif env_name == 'car':
        from config_car import *
    else:
        raise

    #### Get a decent policy. 
    #### Called pi_old because this will be the policy we use to gather data
    policy_old = None
    old_policy_path = os.path.join(model_dir, old_policy_name)
    
    if env_name == 'lake':
        policy_old = LakeDQN(env, 
                             gamma, 
                             action_space_map = action_space_map, 
                             model_type=model_type,
                             position_of_holes=position_of_holes,
                             position_of_goals=position_of_goals, 
                             max_time_spent_in_episode=max_time_spent_in_episode,
                             num_iterations = num_iterations,
                             sample_every_N_transitions = sample_every_N_transitions,
                             batchsize = batchsize,
                             min_epsilon = min_epsilon,
                             initial_epsilon = initial_epsilon,
                             epsilon_decay_steps = epsilon_decay_steps,
                             copy_over_target_every_M_training_iterations = copy_over_target_every_M_training_iterations,
                             buffer_size = buffer_size,
                             num_frame_stack=num_frame_stack,
                             min_buffer_size_to_train=min_buffer_size_to_train,
                             frame_skip = frame_skip,
                             pic_size = pic_size,
                             models_path = os.path.join(model_dir,'weights.{epoch:02d}-{loss:.2f}.hdf5') ,
                             )
    elif env_name == 'car':
        policy_old = CarDQN(env, 
                            gamma, 
                            action_space_map = action_space_map, 
                            action_space_dim=action_space_dim, 
                            model_type=model_type,
                            max_time_spent_in_episode=max_time_spent_in_episode,
                            num_iterations = num_iterations,
                            sample_every_N_transitions = sample_every_N_transitions,
                            batchsize = batchsize,
                            copy_over_target_every_M_training_iterations = copy_over_target_every_M_training_iterations,
                            buffer_size = buffer_size,
                            min_epsilon = min_epsilon,
                            initial_epsilon = initial_epsilon,
                            epsilon_decay_steps = epsilon_decay_steps,
                            num_frame_stack=num_frame_stack,
                            min_buffer_size_to_train=min_buffer_size_to_train,
                            frame_skip = frame_skip,
                            pic_size = pic_size,
                            models_path = os.path.join(model_dir,'weights.{epoch:02d}-{loss:.2f}.hdf5'),
                            )



    else:
        raise
    
    if not os.path.isfile(old_policy_path):
        print 'Learning a policy using DQN'
        policy_old.learn()
        policy_old.Q.model.save(old_policy_path)
    else:
        print 'Loading a policy'
        policy_old.Q.model = load_model(old_policy_path)
        # if env_name == 'car':
        #     try:
        #         # using old style model. This can be deleted if not using provided .h5 file 
        #         policy_old.Q.all_actions_func = K.function([self.model.get_layer('inp').input], [self.model.get_layer('dense_2').output])
        #     except:
        #         pass
        
    # import pdb; pdb.set_trace()
    # print policy_old.Q.evaluate(render=True, environment_is_dynamic=False, to_monitor=True)

    if env_name == 'lake':
        policy_printer = PrintPolicy(size=[map_size, map_size], env=env)
        policy_printer.pprint(policy_old)

    #### Problem setup
    if env_name == 'lake':
        best_response_algorithm = LakeFittedQIteration(state_space_dim + action_space_dim, 
                                                       [map_size, map_size], 
                                                       action_space_dim, 
                                                       max_Q_fitting_epochs, 
                                                       gamma, 
                                                       model_type=model_type, 
                                                       position_of_goals=position_of_goals, 
                                                       position_of_holes=position_of_holes,
                                                       num_frame_stack=num_frame_stack)
        
        fitted_off_policy_evaluation_algorithm = LakeFittedQEvaluation(initial_states, 
                                                           state_space_dim + action_space_dim, 
                                                           [map_size, map_size], 
                                                           action_space_dim, 
                                                           max_eval_fitting_epochs, 
                                                           gamma, 
                                                           model_type=model_type, 
                                                           position_of_goals=position_of_goals, 
                                                           position_of_holes=position_of_holes,
                                                           num_frame_stack=num_frame_stack)
        exact_policy_algorithm = ExactPolicyEvaluator(action_space_map, gamma, env=env, frame_skip=frame_skip, num_frame_stack=num_frame_stack, pic_size = pic_size)
    elif env_name == 'car':
        best_response_algorithm = CarFittedQIteration(state_space_dim, 
                                                      action_space_dim, 
                                                      max_Q_fitting_epochs, 
                                                      gamma, 
                                                      model_type=model_type,
                                                      num_frame_stack=num_frame_stack)
        fitted_off_policy_evaluation_algorithm = CarFittedQEvaluation(state_space_dim, 
                                                                      action_space_dim, 
                                                                      max_eval_fitting_epochs, 
                                                                      gamma, 
                                                                      model_type=model_type,
                                                                      num_frame_stack=num_frame_stack)
        exact_policy_algorithm = ExactPolicyEvaluator(action_space_map, gamma, env=env, frame_skip=frame_skip, num_frame_stack=num_frame_stack, pic_size = pic_size, constraint_thresholds=constraint_thresholds, constraints_cared_about=constraints_cared_about)
    else:
        raise

    online_convex_algorithm = ExponentiatedGradient(lambda_bound, len(constraints), eta)
    exploratory_policy_old = StochasticPolicy(policy_old, 
                                              action_space_dim, 
                                              exact_policy_algorithm, 
                                              epsilon=deviation_from_old_policy_eps, 
                                              prob=prob)
    problem = Program(constraints, 
                      action_space_dim, 
                      best_response_algorithm, 
                      online_convex_algorithm, 
                      fitted_off_policy_evaluation_algorithm, 
                      exact_policy_algorithm, 
                      lambda_bound, 
                      epsilon, 
                      env, 
                      max_number_of_main_algo_iterations,
                      num_frame_stack,
                      pic_size,)    

    lambdas = []
    policies = []

    #### Collect Data
    try:
        print 'Loading Prebuilt Data'
        tic = time.time()
        problem.dataset.data = dd.io.load('%s_new.h5' % env_name)
        print 'Loaded. Time elapsed: %s' % (time.time() - tic)
        # num of times breaking  + distance to center of track + zeros
        if env_name == 'car': 
            tic = time.time()

            # problem.dataset.data['a'] = dd.io.load('%s.h5' % env_name, '/a')
            # problem.dataset.data['x'] = dd.io.load('%s.h5' % env_name, '/x')
            # dataset_length = len(problem.dataset)
            # batch_size = 1024
            # for i in tqdm(range(int(np.ceil(dataset_length/float(batch_size))))):
            
            #     batch_idxs = np.arange(dataset_length)[(i*batch_size):((i+1)*batch_size)]
            #     x = problem.dataset['x'][batch_idxs]

            #     x_repr = policy_old.Q.representation(x)[0]

            #     if len(problem.dataset['x_repr']) == 0:
            #         problem.dataset['x_repr'] = np.empty( (len(problem.dataset),) + x_repr.shape[1:], dtype="float64")
            #         problem.dataset['x_prime_repr'] = np.empty( (len(problem.dataset),) + x_repr.shape[1:], dtype="float64")
                
            #     problem.dataset['x_repr'][batch_idxs] = x_repr

            # del problem.dataset.data['x']

            # problem.dataset.data['x_prime'] = dd.io.load('%s.h5' % env_name, '/x_prime')
            # for i in tqdm(range(int(np.ceil(dataset_length/float(batch_size))))):
            
            #     batch_idxs = np.arange(dataset_length)[(i*batch_size):((i+1)*batch_size)]
            #     x = problem.dataset['x_prime'][batch_idxs]

            #     x_prime_repr = policy_old.Q.representation(x)[0]
                
            #     problem.dataset['x_prime_repr'][batch_idxs] = x_prime_repr

            # # problem.dataset.data['x_prime_preprocess'] = policy_old.Q.representation(dd.io.load('%s.h5' % env_name, '/x_prime'))
            # problem.dataset.data['state_action'] = [problem.dataset.data['x_repr'], problem.dataset.data['a']]
            # problem.dataset.data['c'] = dd.io.load('%s.h5' % env_name, '/c')
            # problem.dataset.data['g'] = dd.io.load('%s.h5' % env_name, '/g')
            # problem.dataset.data['cost'] = dd.io.load('%s.h5' % env_name, '/cost')
            # problem.dataset.data['done'] = dd.io.load('%s.h5' % env_name, '/done')

            # dd.io.save('%s_new.h5' % env_name, problem.dataset.data)
            # import pdb; pdb.set_trace()
            problem.dataset.data['g'] = np.hstack([np.atleast_2d(problem.dataset.data['a'] % 2 == 0).T, problem.dataset.data['g'][:,2:3], problem.dataset.data['g'][:,5:6]]) 
            problem.dataset.data['g'] = (problem.dataset.data['g'] >= constraint_thresholds).astype(int)
            del problem.dataset.data['x']
            del problem.dataset.data['x_prime']
            print 'Preprocessed g. Time elapsed: %s' % (time.time() - tic)
    except:
        print 'Failed to load'
        print 'Recreating dataset'
        num_goal = 0
        num_hole = 0
        dataset_size = 0 
        main_tic = time.time()
        for i in range(max_epochs):
            tic = time.time()
            x = env.reset()
            problem.collect(np.dot(x/255. , [0.299, 0.587, 0.114]), start=True)
            dataset_size += 1
            if env_name in ['car']:  env.render()
            done = False
            time_steps = 0
            episode_cost = 0
            while not done:
                time_steps += 1
                if env_name in ['car']: 
                    # 
                    # epsilon decay
                    exploratory_policy_old.epsilon = 1.-np.exp(-3*(i/float(max_epochs)))
                action = exploratory_policy_old([problem.dataset.current_state()], x_preprocessed=True)[0]

                cost = []
                for _ in range(frame_skip):
                    x_prime, costs, done, _ = env.step(action_space_map[action])
                    cost.append(costs)
                    if done:
                        break
                cost = np.vstack([np.hstack(x) for x in cost]).sum(axis=0)
                early_done, punishment = env.is_early_episode_termination(cost=cost[0], time_steps=time_steps, total_cost=episode_cost)
                # print cost, action_space_map[action] #env.car.fuel_spent/ENGINE_POWER, env.tile_visited_count, len(env.track), env.tile_visited_count/float(len(env.track))
                done = done or early_done

                # if done and reward: num_goal += 1
                # if done and not reward: num_hole += 1
                episode_cost += cost[0] + punishment
                c = (cost[0] + punishment).tolist()
                g = cost[1:].tolist() + [0]
                problem.collect( action,
                                 np.dot(x_prime/255. , [0.299, 0.587, 0.114]),
                                 np.hstack([c,g]).reshape(-1).tolist(),
                                 done
                                 ) #{(x,a,x',c(x,a), g(x,a)^T, done)}
                dataset_size += 1
                x = x_prime
            if (i % 1) == 0:
                print 'Epoch: %s. Exploration probability: %s' % (i, np.round(exploratory_policy_old.epsilon,5), ) 
                print 'Dataset size: %s Time Elapsed: %s. Total time: %s' % (dataset_size, time.time() - tic, time.time()-main_tic)
                if env_name in ['car']: 
                    print 'Performance: %s/%s = %s' %  (env.tile_visited_count, len(env.track), env.tile_visited_count/float(len(env.track)))
                print '*'*20 
        problem.finish_collection(env_name)

    if env_name in ['lake']:
        print 'x Distribution:' 
        print np.histogram(problem.dataset['x'], bins=np.arange(map_size**2+1)-.5)[0].reshape(map_size,map_size)

        print 'x_prime Distribution:' 
        print np.histogram(problem.dataset['x_prime'], bins=np.arange(map_size**2+1)-.5)[0].reshape(map_size,map_size)

        print 'Number episodes achieved goal: %s. Number episodes fell in hole: %s' % (-problem.dataset['c'].sum(axis=0), problem.dataset['g'].sum(axis=0)[0])

        number_of_total_state_action_pairs = (state_space_dim-np.sum(env.desc=='H')-np.sum(env.desc=='G'))*action_space_dim
        number_of_state_action_pairs_seen = len(np.unique(np.hstack([problem.dataset['state_action'][0], problem.dataset['state_action'][1]]),axis=0))
        print 'Percentage of State/Action space seen: %s' % (number_of_state_action_pairs_seen/float(number_of_total_state_action_pairs))

    # print 'C(pi_old): %s. G(pi_old): %s' % (exact_policy_algorithm.run(exploratory_policy_old,policy_is_greedy=False, to_monitor=True) )
    ### Solve Batch Constrained Problem
    
    iteration = 0
    while not problem.is_over(policies, lambdas, infinite_loop=True):
        iteration += 1
        K.clear_session()
        # policy_printer.pprint(policies)
        print '*'*20
        print 'Iteration %s' % iteration
        print
        if len(lambdas) == 0:
            # first iteration
            lambdas.append(online_convex_algorithm.get())
            print 'lambda_{0} = {1}'.format(iteration, lambdas[-1])
        else:
            # all other iterations
            lambda_t = problem.online_algo()
            lambdas.append(lambda_t)
            print 'lambda_{0} = online-algo(pi_{1}) = {2}'.format(iteration, iteration-1, lambdas[-1])

        lambda_t = lambdas[-1]
        pi_t = problem.best_response(lambda_t, desc='FQI pi_{0}'.format(iteration), exact=exact_policy_algorithm)

        # policies.append(pi_t)
        problem.update(pi_t, iteration) #Evaluate C(pi_t), G(pi_t) and save

if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description='Choose environment.')
    parser.add_argument('-env', dest='env', help='lake/car openAI environment')
    parser.add_argument('--headless', dest='headless', action='store_true',
                        help = 'Use flag if running on server so you can run render() from openai')
    parser.set_defaults(headless=False)
    args = parser.parse_args()
    

    assert args.env in ['lake', 'car'], 'Need to choose between FrozenLakeEnv (lake) or Car Racing (car) environment'


    main(args.env, args.headless)