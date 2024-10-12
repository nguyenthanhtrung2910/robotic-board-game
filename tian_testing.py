"""
testing trained enviroment
"""
import torch
import gymnasium

from src.game.consts import *
from src.game import robotic_board_game

from tianshou.data import Batch
from torch import nn
from tianshou.policy import DQNPolicy
from tianshou.utils.net.common import Net

env = robotic_board_game.Game(colors_map='assets/csv_files/colors_map.csv',
                              targets_map='assets/csv_files/targets_map.csv',
                              required_mail=6,
                              number_robots_per_player=1,
                              agent_colors=['r','b'],
                              render_mode='human',
                              with_battery=True)
v_head = dict()
q_head = dict()
net = Net(
    state_shape=env.observation_space(env.agents[0])['observation'].shape,
    action_shape=env.action_space(env.agents[0]).n,
    norm_layer=nn.LayerNorm,
    dueling_param=[q_head, v_head],
    hidden_sizes=[256, 256, 128, 128, 64, 64],
    device="cuda" if torch.cuda.is_available() else "cpu",
).to("cuda" if torch.cuda.is_available() else "cpu")
optim = torch.optim.Adam(net.parameters(), lr=0.0001)
policy = DQNPolicy(
    model=net,
    optim=optim,
    action_space=gymnasium.spaces.Discrete(5),
    discount_factor=0.99,
    estimation_step=20,
    target_update_freq=1,
    is_double=True,
)

policy.load_state_dict(torch.load('DuelDQN_for_2_robots.pth', weights_only=True, map_location=torch.device('cpu')))
policy.set_eps(0)
policy.eval()
obs, reward, termination, truncation, info = env.last()
while not termination and not truncation:
    action = policy(Batch(obs=Batch(obs=obs['observation'].reshape(1, -1), mask=obs['action_mask'].reshape(1,-1)), info=[])).act[0]
    print(env.agent_selection, action)
    env.step(action)
    obs, reward, termination, truncation, info = env.last()
print(env.num_steps)
env.close()