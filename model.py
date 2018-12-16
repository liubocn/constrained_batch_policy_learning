"""
Created on December 16, 2018

@author: clvoloshin, 
"""

import numpy as np

class Model(object):
    def __init__(self):
        '''
        Abstract class defining which functions a model should have
        '''
        self.model = None

    def copy_over_to(self, to_):
        NotImplemented

    def fit(self, X, y, verbose=0):
        NotImplemented

    def predict(self, X_a):
        NotImplemented

    def all_actions(self, X):
        NotImplemented

    def evaluate(self, verbose=False, render=False):
        return self.policy_evalutor.run(self, verbose=verbose, render=render)

    def min_over_a(self, X, randomized_tiebreaking=False):
        '''
        Returns min_a Q(X,a), argmin_a Q(X,a)
        '''

        Q_x_a = self.all_actions(X)
        return self.min_and_argmin(Q_x_a, randomized_tiebreaking, axis=1)

    def max_over_a(self, X, randomized_tiebreaking=False):
        '''
        Returns min_a Q(X,a), argmin_a Q(X,a)
        '''

        Q_x_a = self.all_actions(X)
        return self.max_and_argmax(Q_x_a, randomized_tiebreaking, axis=1)

    @staticmethod
    def max_and_argmax(Q, randomized_tiebreaking=False, **kw):
        ''' max + Argmax + Breaks max/argmax ties randomly'''
        if not randomized_tiebreaking:
            return np.max(Q, **kw), np.argmax(Q, **kw)
        else:
            tie_breaker = np.random.random(Q.shape) * (Q==Q.max())
            argmax = np.argmax(tie_breaker, **kw) # this is counter intuitive.
            return Q[np.arange(Q.shape[0]), argmax], argmax

    @staticmethod
    def min_and_argmin(Q, randomized_tiebreaking=False, **kw):
        ''' min + Argmin + Breaks min/argmin ties randomly'''
        if not randomized_tiebreaking:
            return np.min(Q, **kw), np.argmin(Q, **kw)
        else:
            tie_breaker = - np.random.random(Q.shape) * (Q==Q.min())
            argmin = np.argmin(tie_breaker, **kw)
            return Q[np.arange(Q.shape[0]), argmin], argmin

    def __call__(self, *args):
        if len(args) == 1:
            '''
            Run policy: pi = argmin_a Q(x,a)
            '''
            x = args[0]
            return self.min_over_a(x, False)[1]
        elif len(args) == 2:
            '''
            Evaluate Q(x,a)
            '''
            x,a = args
            return self.predict(np.hstack([x, np.eye(self.dim_of_actions)[a]  ]))
        else:
            raise

    @staticmethod
    def cartesian_product(x,y):
        return np.hstack([np.tile(x.T, y.shape[1]).T, np.tile(y,x.shape[0]).reshape(-1,y.shape[1])])
