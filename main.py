import pygame
import logging as log
import argparse

from src.game.robotic_board_game import Game
from src.agents.astar_agent import AStarAgent

pygame.init()

parser = argparse.ArgumentParser()
parser.add_argument("--color_map", 
                    help="chose colors map",
                    type=str,
                    default="assets/csv_files/colors_map.csv")
parser.add_argument("--target_map", 
                    help="chose targets map",
                    type=str,
                    default="assets/csv_files/targets_map.csv")

parser.add_argument("--required_mail",
                    help="chose required mail to win",
                    type=int)
parser.add_argument("--robot_colors",
                    help="chose robot colors",
                    nargs="+",
                    choices=['r', 'b', 'o', 'gr', 'y'])
parser.add_argument("--number_robots_per_player",
                    help="chose number robots per player. It shouldn't more than 6",
                    type=int,
                    default=1,
                    choices=[1, 2, 3, 4, 5, 6])
parser.add_argument("--with_battery",
                    help="battery is considered or not",
                    action='store_true')
parser.add_argument("--random_steps_per_turn",
                    help="allow ramdom number steps per turn or not",
                    action='store_true')
parser.add_argument("--max_step",
                    help="maximum game's step",
                    type=int,
                    default=800)

parser.add_argument("--render_mode",
                    help="render mode",
                    type=str,
                    default="human",
                    choices=["human", "None"])
parser.add_argument("--number_persons",
                    help="chose number person-players",
                    type=int,
                    default=0)
parser.add_argument("--number_runs",
                    help="number of runs",
                    type=int,
                    default=1)
parser.add_argument("--logger",
                    help="log to file or not",
                    action='store_true')

args = parser.parse_args()
render_mode = None if args.render_mode == "None" else args.render_mode
assert args.number_persons <= len(args.robot_colors), "Number person-players can't be bigger than number players "
if args.logger:
    log.basicConfig(level=log.INFO,
                    filename="events.log",
                    filemode="w",
                    format="%(levelname)s: %(message)s")

agents = []
game = Game(args.color_map, 
            args.target_map, 
            required_mail=args.required_mail, 
            agent_colors=args.robot_colors,
            number_robots_per_player=args.number_robots_per_player,
            with_battery=args.with_battery,
            random_steps_per_turn=args.random_steps_per_turn,
            max_step=args.max_step,
            render_mode=render_mode,
            log_to_file=args.logger)

maximum_battery = game.robots[game.agent_selection].battery if args.with_battery else None
astar = AStarAgent(game.observation_space(game.agent_selection),
                    args.color_map,
                    args.target_map, 
                    maximum_battery,
                    )

for _ in range(len(game.agents) - args.number_persons*args.number_robots_per_player):
    agents.append(astar)
    
i = 0
while i < args.number_runs:
    winner, time = game.run(agents)
    if winner:
        print(winner, time)
        i += 1
