import re
import os
import importlib
import argparse
from pprint import pprint
from typing import Any

import yaml
import pygame
from yaml.loader import Loader
from yaml.nodes import MappingNode

from src.agents.rl_agent import RLAgent
from src.game.robotic_board_game import Game

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config", 
    default=os.path.join('configs', 'config.yaml'),
    help="path to configuration .yaml file",
    type=str,
)

args = parser.parse_args()
def set_class(config: dict[str, Any], key: str) -> None:
    class_path = config[key]
    module_path, class_name = class_path.rsplit(".", 1)
    config[key] = getattr(importlib.import_module(module_path), class_name)

with open(args.config, "r") as file:
    yaml_content =re.sub(r"(agent\d:)", r"\1 !agent", file.read())\
                    .replace("agent:", "agent: !agent")
    
def agent_constructor(loader: Loader, node: MappingNode):
    data = loader.construct_mapping(node, deep=True)
    try:
        set_class(data, 'agent_type')
        agent_type = data.pop('agent_type')
        set_class(data, 'model')
        set_class(data, 'policy')
        set_class(data['model_args'], 'norm_layer')
        set_class(data['model_args'], 'activation')
        set_class(data['model_args'], 'linear_layer')
        set_class(data['model_args']['dueling_param'], 'norm_layer')
        set_class(data['model_args']['dueling_param'], 'activation')
        set_class(data['model_args']['dueling_param'], 'linear_layer')
    except KeyError:
        pass
    return agent_type(**data)
  
yaml.add_constructor('!agent', agent_constructor) 
agent = yaml.load(yaml_content, Loader=yaml.FullLoader)['agent']

print(agent.policy.model)
training_stats = agent.train()
pprint(training_stats)
