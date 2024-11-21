import re
import os
import importlib
import argparse
from typing import Any

import yaml
import pygame
from yaml.loader import Loader
from yaml.nodes import MappingNode

from src.game.robotic_board_game import Game

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config", 
    default=os.path.join('configs', 'animate_config_template.yaml'),
    help="path to configuration .yaml file",
    type=str,
)

args = parser.parse_args()
def set_class(config: dict[str, Any], key: str) -> None:
    try:
        class_path = config[key]
        module_path, class_name = class_path.rsplit(".", 1)
        config[key] = getattr(importlib.import_module(module_path), class_name)
    except KeyError:
        pass

with open(args.config, "r") as file:
    yaml_content =re.sub(r"(agent\d:)", r"\1 !agent", file.read())\
                    .replace("agent:", "agent: !agent")\
                    .replace("env:", "env: !env")\
                
def env_constructor(loader: Loader, node: MappingNode):
    data = loader.construct_mapping(node, deep=True)
    data['render_mode'] = 'human'
    return Game(**data)
    
def agent_constructor(loader: Loader, node: MappingNode):
    data = loader.construct_mapping(node, deep=True)
    count = data.pop('count', 1)
    data.pop('memory_class', None)
    data.pop('memory_args', None)
    set_class(data, 'agent_class')
    agent_type = data.pop('agent_class')
    set_class(data, 'model_class')
    set_class(data, 'policy_class')
    set_class(data['model_args'], 'norm_layer')
    set_class(data['model_args'], 'activation')
    set_class(data['model_args'], 'linear_layer')
    for i in range(2):
        set_class(data['model_args']['dueling_param'][i], 'norm_layer')
        set_class(data['model_args']['dueling_param'][i], 'activation')
        set_class(data['model_args']['dueling_param'][i], 'linear_layer')
    return [agent_type(**data)]*count
  
yaml.add_constructor('!agent', agent_constructor) 
yaml.add_constructor('!env', env_constructor) 
data = yaml.load(yaml_content, Loader=yaml.FullLoader)

env = data.pop('env')
agents = [item for sublist in data.values() for item in sublist]
print(env.run(agents))