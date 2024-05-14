import torch
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv
from tianshou.env.pettingzoo_env import PettingZooEnv
from tianshou.policy import DQNPolicy, MultiAgentPolicyManager
from tianshou.utils.net.common import Net
from Game import Game
from Game import Board
from copy import deepcopy


def get_env(render_mode = None):
    board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
    game = Game.Game(board, 1, 1, ['r', 'b'] ,render_mode=render_mode)
    game = PettingZooEnv(game)
    return game

game = get_env(render_mode='human')
net1 = Net(
    state_shape=game.observation_space['observation'].shape,
    action_shape=game.action_space.n,
    hidden_sizes=[128, 128, 128, 128],
    device="cuda" if torch.cuda.is_available() else "cpu",
).to("cuda" if torch.cuda.is_available() else "cpu")
optim1 = torch.optim.Adam(net1.parameters(), lr=1e-3)
policy1 = DQNPolicy(
    model=net1,
    optim=optim1,
    discount_factor=0.95,
    estimation_step=3,
    target_update_freq=320,
)
policy1.load_state_dict(torch.load('log/ttt/dqn/policy.pth'))
policy2 = deepcopy(policy1)

policy = MultiAgentPolicyManager([policy1, policy2], game)
game = DummyVectorEnv([lambda: game])
policy.eval()
for p in policy.policies.values():
    p.set_eps(0)
collector = Collector(policy, game, VectorReplayBuffer(20_000, len(game)), exploration_noise=True)
result = collector.collect(n_episode=1, render=1)
print(collector.buffer.sample(0)[0].act)