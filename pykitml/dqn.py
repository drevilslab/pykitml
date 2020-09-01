import random
from abc import ABC, abstractmethod
from collections import deque

import numpy as np
import matplotlib.pyplot as plt

import tqdm

from .network import NeuralNetwork
from .pklhandler import save

'''
    Ref: https://github.com/keon/deep-q-learning/blob/master/ddqn.py
'''

__all__ = ['DQNAgent', 'Environment']

class ReplayBuffer:
    def __init__(self, state_size, buffer_size):
        self._size = buffer_size
        self._ptr = 0
        self._len = 0
        
        self._states = np.zeros((buffer_size, state_size))
        self._actions = np.zeros((buffer_size), dtype=int)
        self._rewards = np.zeros((buffer_size))
        self._next_states = np.zeros((buffer_size, state_size))
        self._done = np.zeros((buffer_size), dtype=bool)

    def __len__(self):
        return self._len

    def append(self, state, action, reward, next_state, done):
        if(self._len != self._size): self._len += 1
        if(self._ptr == self._size): self._ptr = 0

        ptr = self._ptr
        self._states[ptr] = state
        self._actions[ptr] = action
        self._rewards[ptr] = reward
        self._next_states[ptr] = next_state
        self._done[ptr] = done

        self._ptr += 1

    def sample(self, batch_size):
        indices = np.random.choice(self._len, batch_size)

        return (self._states[indices], self._actions[indices],
            self._rewards[indices], self._next_states[indices],
            self._done[indices])

class DQNAgent:
    '''
    This class implements Double Deep Q Learning for RL. Use a Neural Network
    with huber loss for predicting Q values.
    '''

    def __init__(self, layer_sizes, mem_size=10000):
        '''
        Parameters
        ----------
        layer_sizes : list
            A list of integers describing the number of layers and the number of neurons in each
            layer. For e.g. :code:`[784, 100, 100, 10]` describes a network with one input
            layer having 784 neurons, two hidden LSTM layers having 100 neurons each and a 
            dense output layer with 10 neurons.
        mem_size : int
            The size for storing experience replay.       
        '''
        self._model = NeuralNetwork(layer_sizes, config='leakyrelu-identity-huber')
        self._target_model = NeuralNetwork(layer_sizes, config='leakyrelu-identity-huber')
        self._target_model._mparams = np.array(self._model._mparams, copy=True)

        self._act_size = layer_sizes[-1]
        self._state_size = layer_sizes[0]

        self._memory = ReplayBuffer(layer_sizes[0], mem_size)

        self._save_freq = 0
        self._filename = ''
    
    def _train_minibatch(self, batch_size, optimizer, discount_factor):
        if(batch_size > len(self._memory)): return

        # Sample a mini batch
        states, actions, rewards, next_states, done = self._memory.sample(batch_size)
        
        # Calculate target qvals
        self._target_model.feed(next_states)
        target_qvals = np.where(done,
            rewards,
            rewards + discount_factor*np.amax(self._target_model.get_output(), axis=1)
        )

        # Train
        for i in range(batch_size):
            self._model.feed(np.array([states[i]]))
            target = np.array(self._model.get_output(), copy=True)
            target[actions[i]] = target_qvals[i]
            grad = self._model._backpropagate(0, target)
            self._model._mparams = optimizer._optimize(self._model._mparams, grad)
                

    def train(self, env, nepisodes, optimizer, batch_size=64, render=False,
        explr_rate=1, explr_min=0.01, explr_decay=0.99, disc_factor=0.95):
        '''
        Trains the agent on the given environment using deep Q learning.

        Parameters
        ----------
        env : obj
            Object that represents the environment. See :ref:`environment`
        nepisodes : int
            Number of episodes to train for.
        optimizer : any Optimizer object
            See :ref:`optimizers`
        batch_size : int
            How many samples from replay experience to train on on each step.
        render : bool
            If set to true, will call the :code:`render()` method in :code:`env`
            object.
        explr_rate : float
            Initial exploration rate. Higher the exploration rate,
            agent will take more random actions.
        explr_min : float
            Minimum exploration rate.
        explr_decay : float
            Multiplication factor for reducing exploration rate after
            each episode.
        disc_factor : float
            Discount factor, value of future rewards.
        '''

        self._reward_graph = []

        pbar = tqdm.trange(0, nepisodes, ncols=80, unit='episodes')
        for e in pbar:
            # Play an episode in the environment
            done = False
            state = env.reset()
            total_rewards = 0
            total_steps = 0        
            while not done:
                if(random.random() <= explr_rate):
                    action = random.randint(0, self._act_size-1)
                else:
                    self._model.feed(state)
                    qval = self._model.get_output()
                    action = np.argmax(qval)

                next_state, reward, done = env.step(action)
                if(render): env.render()

                # Track metrics
                total_rewards += reward
                total_steps += 1
                
                # Store in replay memory
                self._memory.append(state, action, reward, next_state, done)
                state = next_state

                # Sample mini batch and train
                self._train_minibatch(batch_size, optimizer, disc_factor)

            # Decrase exploration rate
            if(explr_rate > explr_min): explr_rate*=explr_decay

            # Update target model
            self._target_model._mparams = np.array(self._model._mparams, copy=True)

            # Update progress bar
            pbar.set_postfix(steps=total_steps, rewards=total_rewards)
            self._reward_graph.append(total_rewards)

            # Save agent
            if(self._save_freq != 0):
                if((e+1)%self._save_freq == 0): 
                    save(self, self._filename+'_episode'+str(e)+'.pkl')

        env.close()

    def set_save_freq(self, freq, name):
        '''
        Saves the agent model every :code:`freq` episodes during training.

        Parameters
        ----------
        freq : int
            Saving frequency in episodes.
        name : str
            Name of the file.
        '''
        self._save_freq = freq
        self._filename = name

    def plot_performance(self):
        '''
        Plots logged performance data after training. 
        Should be called after :py:func:`train`.

        Raises
        ------
        AttributeError
            If the model has not been trained, i.e :py:func:`train` has
            not been called before.        
        '''
        def running_mean(x, N):
            cumsum = np.cumsum(np.insert(x, 0, 0)) 
            return (cumsum[N:] - cumsum[:-N]) / float(N)

        plt.figure('Performance graph', figsize=(10, 7))
        plt.plot(running_mean(self._reward_graph, 30))
        plt.show()

class Environment(ABC):
    @abstractmethod
    def reset(self):
        '''
        Resets the environment and returns initial state.

        Returns
        -------
        initial_state : np.array
            The initial state of the environment as a numpy array.
        '''
        pass

    @abstractmethod
    def step(self, action):
        '''
        Performas given action, modifies current state to next state, 
        returns next state, reward and a bool to tell weather the episode has
        terminated.

        Returns
        -------
        next_state : np.array
            The next state of the environment as a numpy array.
        reward : int
            An integer telling the agent how well it performed.
        done : bool
            Flag to tell weather the environment has reached a terminal
            state.
        '''
        pass

    @abstractmethod
    def close(self):
        '''
        Called after training is completely, properly closes/exists
        the environment.
        '''
        pass

    def render(self):
        '''
        Method to render the environment, show a visual representation
        of the environment.
        '''
        pass
