from src import a_star_agent
from src.game import robotic_board_game

game = robotic_board_game.Game(colors_map='assets/csv_files/colors_map.csv',
                              targets_map='assets/csv_files/targets_map.csv', 
                              required_mail=6, 
                              number_robots_per_player=1, 
                              agent_colors=['gr', 'b', 'o', 'r'], 
                              render_mode='human',
                              with_battery=True)
obs, reward, termination, truncation, info = game.last()
agent = a_star_agent.AStarAgent(colors_map='assets/csv_files/colors_map.csv', 
                                targets_map='assets/csv_files/targets_map.csv', 
                                number_robots=game.number_robots, 
                                maximum_battery=50)
rewards = 0
while not termination and not truncation:
    action = agent.get_action(obs)
    print(obs['observation'])
    print(action)
    game.step(action)
    next_obs, reward, termination, truncation, info = game.last()
    print(game.previous_agent, game._cumulative_rewards[game.previous_agent])
    if game.agent_selection == game.agents[1]:
        rewards += game._cumulative_rewards[game.previous_agent]
    print(game.observe(game.previous_agent)['observation'])
    print('\n')
    obs = next_obs
print(game.num_steps)
print(game.winner)
print(rewards)
game.close()