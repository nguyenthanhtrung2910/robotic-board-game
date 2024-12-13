from typing import Any
import importlib
import os

import yaml
import torch

from rbgame.agent.astar_agent import AStarAgent
from rbgame.agent.rl_agent import OffPolicyAgent

def set_class(config: dict[str, Any], key: str) -> None:
    """
    Transform class name in to class. Do nothing if :code:`key` not found.

    :param config: Dict with value can be a class name.
    :param key: Key that have value is modified.
    """
    try:
        class_path = config[key]
        module_path, class_name = class_path.rsplit(".", 1)
        config[key] = getattr(importlib.import_module(module_path), class_name)
    except KeyError:
        pass

def get_object(config: dict[str, Any]) -> object:
    """
    Remove class from :code:`config` and return the object, constructed with this class.

    :param config: Arguments to construct object, including the class.
    :return: The constructed object.
    """
    set_class(config, 'type')
    type = config.pop('type')
    return type(**config)
    
def dqn_constructor(num_robots: int, with_battery: bool) -> OffPolicyAgent:
    """
    Initialize a py:class:`OffPolicyAgent` and load weight to this from checkpoint.

    :param num_robots: Number robots of the game.
    :param with_battery: Battery is considered or not.
    :return: The agent.
    """
    ckpt = str(num_robots)+'-b' if with_battery else str(num_robots)
    with open(os.path.join(os.getcwd(), 'checkpoints', ckpt, 'policy.yaml'), "r") as file:
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
    policy.load_state_dict(torch.load(
        os.path.join(os.getcwd(), 'checkpoints', ckpt, 'best.pth'), 
        weights_only=True, 
        map_location=torch.device(policy.model.device),
        )
    )
    agent = OffPolicyAgent(policy)
    return agent

def astar_constructor(num_robots: int, with_battery: bool) -> AStarAgent:
    """
    Initialize a :py:class:`AStarAgent`.

    :param num_robots: Number robots of the game.
    :param with_battery: Battery is considered or not.
    :return: The agent.
    """
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    agent = AStarAgent(
        colors_map=os.path.join(parent_dir, 'assets', 'csv_files', 'colors_map.csv'),
        targets_map=os.path.join(parent_dir, 'assets', 'csv_files', 'targets_map.csv'),
        num_robots=num_robots,
        maximum_battery=10 if with_battery else None,
    )
    return agent