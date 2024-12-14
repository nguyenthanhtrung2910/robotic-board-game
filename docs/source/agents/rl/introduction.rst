Introduction
============

Using reinforcement learning algorithms gives us some advantages:

* Agent is trainable so it's smarter 😀.
* Agent can parallel play in many environment because neural network 
  accepts a batch of observations as input.

In Reinforcement Learning we have process: 

.. figure:: ../../_static/agent_and_env_diag.svg
    :align: center
    :alt: The interaction between the environment and the agent.
    :width: 600

    The interaction between the environment and the agent.

Here is what happen:

* At a given time step :math:`t`, the environment is in a state :math:`\boldsymbol{s_t}`, which results in the 
  observation :math:`\boldsymbol{o_t}`.

* Based on :math:`\boldsymbol{o_t}` and its internal policy function, the agent calculates an action :math:`\boldsymbol{a_t}`.

* Based on both the state :math:`\boldsymbol{s_t}` and the action :math:`\boldsymbol{a_t}`, and according to 
  its internal dynamics, the environment updates its state to :math:`\boldsymbol{s_{t+1}}`, which results in 
  the next observation :math:`\boldsymbol{o_{t+1}}`.

* Based on :math:`\boldsymbol{s_t}`, :math:`\boldsymbol{a_t}`, and :math:`\boldsymbol{s_{t+1}}`, the environment 
  also calculates a scalar reward :math:`\boldsymbol{r_t}` and flag :math:`\boldsymbol{done}`, which shows 
  whether the environment ends at the current step or not. The reward is an immediate measure of how good the 
  action :math:`\boldsymbol{a_t}` is.

* Transition :math:`(\boldsymbol{o_t}, \boldsymbol{a_t}, \boldsymbol{o_{t+1}}, \boldsymbol{r_t}, \boldsymbol{done})` 
  is saved to its memory (or replay buffer).

* At the next time step :math:`t+1` the agent receives the observation :math:`\boldsymbol{o_{t+1}}` to generate 
  next action :math:`\boldsymbol{a_{t+1}}` and the process is repeated.

* After specific number of steps, agent samples transitions from memory and update its policy (in fact, update neural network)
  based on sampled transitions. How many transitions are sampled and how agent update policy? It depends on difference algorithms.