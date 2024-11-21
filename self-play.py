import re
import os
import importlib
import argparse
from pprint import pprint
from typing import Any

import yaml
import numpy as np
import torch
import pygame
from yaml.loader import Loader
from yaml.nodes import MappingNode
from src.trainer import MultiAgentTrainer

parser = argparse.ArgumentParser()
parser.add_argument(
    "--config", 
    default=os.path.join('configs', 'training_config_template.yaml'),
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
    
def agent_constructor(loader: Loader, node: MappingNode):
    data = loader.construct_mapping(node, deep=True)
    count = data.pop('count', 1)
    set_class(data, 'agent_class')
    agent_type = data.pop('agent_class')
    set_class(data, 'model_class')
    set_class(data, 'policy_class')
    set_class(data, 'memory_class')
    set_class(data['model_args'], 'norm_layer')
    set_class(data['model_args'], 'activation')
    set_class(data['model_args'], 'linear_layer')
    for i in range(2):
        set_class(data['model_args']['dueling_param'][i], 'norm_layer')
        set_class(data['model_args']['dueling_param'][i], 'activation')
        set_class(data['model_args']['dueling_param'][i], 'linear_layer')
    return [agent_type(**data)]*count

def trainer_constructor(loader: Loader, node: MappingNode):
    data = loader.construct_mapping(node, deep=True)
    return MultiAgentTrainer(**data)

with open(args.config, "r") as file:
    yaml_content =re.sub(r"(agent\d:)", r"\1 !agent", file.read())\
                    .replace("agent:", "agent: !agent")\
                    .replace("trainer:", "trainer: !trainer")
    
yaml.add_constructor('!agent', agent_constructor) 
yaml.add_constructor('!trainer', trainer_constructor)

data = yaml.load(yaml_content, Loader=yaml.FullLoader)

agents = data['agent']
trainer = data['trainer']
assert data['max_eps'] >= data['min_eps']
assert data['end_beta'] >= data['begin_beta']

def train_fn(episode: int, step: int) -> None:
    agents[0].policy.set_eps(np.maximum(data['max_eps']*data['eps_rate']**episode, data['min_eps']))
    agents[0].memory.set_beta(data['end_beta'] + (data['begin_beta'] - data['end_beta']) * np.exp(-data['beta_rate'] * episode))

def save_best_fn(episode: int) -> None:
    if episode > data['episode_to_save']:
        torch.save(agents[0].policy.state_dict(), data['best_ckpt'])

def save_last_fn() -> None:
    torch.save(agents[0].policy.state_dict(), data['last_ckpt'])

def stop_fn(reward: float, episode: int) -> bool:
    return reward > data['reward_to_stop']

trainer.train_fn = train_fn
trainer.save_best_fn = save_best_fn
trainer.save_last_fn = save_last_fn
trainer.stop_fn = stop_fn
print(agents[0].policy.model)
pprint(trainer.train(agents, [i == 0 for i,_ in enumerate(agents)]))