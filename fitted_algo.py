"""
Created on December 12, 2018

@author: clvoloshin, 
"""

from model import Model
import numpy as np

class FittedAlgo(object):
	def __init__(self, num_inputs, dim_of_actions, max_epochs, gamma):
		'''
		An implementation of fitted Q iteration

		num_inputs: number of inputs
		dim_of_actions: dimension of action space
		max_epochs: positive int, specifies how many iterations to run the algorithm
		gamma: discount factor
		'''
		self.num_inputs = num_inputs
		self.dim_of_actions = dim_of_actions
		self.max_epochs = max_epochs
		self.gamma = gamma

	def init_Q(self):
		return Model(self.num_inputs, 1, self.dim_of_actions)

	def fit(self, X, y):
		# D_k = {(X,y)} is the dataset of the kth iteration of Fitted Q
		try:
			self.Q_k.fit(X, y)
		except NameError:
			print 'Q has not been initialized. Please call run before calling fit.'
			sys.exit()


	def run(self, dataset):
		'''
		Abstract function
		'''
		pass


