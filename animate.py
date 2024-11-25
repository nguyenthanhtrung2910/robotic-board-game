import importlib
import argparse
from typing import Any

import yaml
import torch
import pygame

from src.game.robotic_board_game import Game
from src.agents.rl_agent import OffPolicyAgent
from src.agents.astar_agent import AStarAgent
def set_class(config: dict[str, Any], key: str) -> None:
    try:
        class_path = config[key]
        module_path, class_name = class_path.rsplit(".", 1)
        config[key] = getattr(importlib.import_module(module_path), class_name)
    except KeyError:
        pass

def get_object(config: dict[str, Any]) -> None:
    set_class(config, 'type')
    type = config.pop('type')
    return type(**config)

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
                    type=int,
                    default=10)
parser.add_argument("--robot_colors",
                    help="chose robot colors",
                    nargs="+",
                    choices=['r', 'b', 'o', 'gr', 'y'],
                    default=['r', 'b'])
parser.add_argument("--num_robots_per_player",
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
                    default=1000)
for i in range(1, 6):
    parser.add_argument(f"--agent{i}",
                        nargs="+",
        )

args = parser.parse_args()
game = Game(
    args.color_map, 
    args.target_map, 
    required_mail=args.required_mail, 
    robot_colors=args.robot_colors,
    num_robots_per_player=args.num_robots_per_player,
    with_battery=args.with_battery,
    random_num_steps=args.random_steps_per_turn,
    max_step=args.max_step,
    render_mode='human',
    log_to_file=False,
    )
agents = []
for j in range(1, 6):
    agent_details = getattr(args, f'agent{j}')
    if agent_details is not None: 
        if agent_details[0] == 'dqn': 
            with open(agent_details[2], "r") as file:
                data = yaml.safe_load(file)
                            
            set_class(data['model'], 'norm_layer')
            set_class(data['model'], 'activation')
            set_class(data['model'], 'linear_layer')
            for i in range(2):
                set_class(data['model']['dueling_param'][i], 'norm_layer')
                set_class(data['model']['dueling_param'][i], 'activation')
                set_class(data['model']['dueling_param'][i], 'linear_layer')
            set_class(data['optim'], 'type')

            data['model'] = get_object(data['model'])
            data['optim'] = data['optim']['type'](data['model'].parameters())
            data['action_space'] = get_object(data['action_space'])
            policy=get_object(data)
            if agent_details[3] is not None:
                policy.load_state_dict(
                    torch.load(
                        f=agent_details[3], 
                        weights_only=True, 
                        map_location=torch.device(policy.model.device),
                        )
                    )
            agent=OffPolicyAgent(policy)
            agents.extend([agent]*int(agent_details[1]))
        elif agent_details[0] == 'astar':
            agent = AStarAgent(
                colors_map=args.color_map,
                targets_map=args.target_map,
                num_robots=game.num_robots,
                maximum_battery=game.robots[game.agent_selection].battery if args.with_battery else None,
            )
            agents.extend([agent]*int(agent_details[1]))
        else:
            raise ValueError('No available agent type.')
print(game.run(agents))