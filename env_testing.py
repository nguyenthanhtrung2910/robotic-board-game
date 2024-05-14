from Game import Game
from Game import Board
from Agents import DefaultAgent, VirtualBoard

board = Board.Board('csv_files/colors_map.csv', 'csv_files/targets_map.csv')
game = Game.Game(board, 1, 2, ['r', 'b'], render_mode='human')
obs, reward, termination, truncation, info = game.last()
agent1 = DefaultAgent.DefaultAgent('r',VirtualBoard.VirtualBoard('csv_files/colors_map.csv', 'csv_files/targets_map.csv'),1, game.state)
agent2 = DefaultAgent.DefaultAgent('b',VirtualBoard.VirtualBoard('csv_files/colors_map.csv', 'csv_files/targets_map.csv'),1, game.state)
agent = {'r': agent1, 'b':agent2}
while not termination and not truncation:
    action = agent[game.agent_selection].policy(game.state)
    game.step(action)
    obs, reward, termination, truncation, info = game.last()
    print(game.agent_selection, obs, game._cumulative_rewards)
game.close()