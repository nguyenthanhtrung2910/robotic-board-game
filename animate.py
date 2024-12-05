from typing import Any
import os
import importlib

import pygame_menu.events
import yaml
import torch
import pygame
import pygame_menu
pygame.init()

from src.game.robotic_board_game import Game
from src.agents.base_agent import BaseAgent
from src.agents.rl_agent import OffPolicyAgent
from src.agents.astar_agent import AStarAgent
from src.game.consts import *

surface = pygame.display.set_mode((15*CELL_SIZE[0], 11*CELL_SIZE[1]))
main_menu = pygame_menu.Menu(
    'Welcome', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
    theme=pygame_menu.themes.THEME_BLUE,
    onclose=pygame_menu.events.CLOSE,
)
setting_menu = pygame_menu.Menu(
    'Setting', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
    theme=pygame_menu.themes.THEME_BLUE,
)
result_menu = pygame_menu.Menu(
    'Result', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
    theme=pygame_menu.themes.THEME_BLUE,
    onclose=pygame_menu.events.CLOSE,
)
error_menu = pygame_menu.Menu(
    'Error', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
    theme=pygame_menu.themes.THEME_BLUE,
    onclose=pygame_menu.events.CLOSE,
)
env_args = {
    'colors_map': 'assets/csv_files/colors_map.csv',
    'targets_map': 'assets/csv_files/targets_map.csv',
    'required_mail': 10,
    'robot_colors': ['r', 'b'],
    'num_robots_per_player': 1,
    'with_battery': False,
    'random_num_steps': False,
    'max_step': 1000,
    'render_mode': 'human',
    'player1': 'dqn',
    'player2': 'dqn',
    'player3': 'dqn',
    'player4': 'dqn',
}
def set_required_mail(range_value: int) -> None:
    env_args['required_mail'] = range_value

def set_player_colors(items: tuple[Any, list[int]]) -> None:
    item_values, _ = items
    env_args['robot_colors'] = [item_value[1] for item_value in item_values]

def set_player_type(items: tuple[Any, int], a: int, i: int) -> None:
    env_args[f'player{i}'] = a

def set_num_robot_per_player(items: tuple[Any, int], a: int) -> None:
    env_args['num_robots_per_player'] = a

def set_max_step(current_text: int) -> None:
    env_args['max_step'] = current_text

def set_with_battery(current_state_value: bool) -> None:
    env_args['with_battery'] = current_state_value

def set_random_step_per_turn(current_state_value: bool) -> None:
    env_args['random_num_steps'] = current_state_value

def run_game() -> None:
    if len(env_args['robot_colors']) <= 1:
        error_menu.enable()
        error_menu.mainloop(surface)
        return
    agents = []
    for i in range(4):
        agent_type = env_args.pop(f'player{i+1}', None)
        if i < len(env_args['robot_colors']):
            agents.extend(init_agent(agent_type, 
                                     env_args['num_robots_per_player'], 
                                     env_args['num_robots_per_player']*len(env_args['robot_colors']),
                                     env_args['with_battery']))
    game = Game(**env_args)
    main_menu.close()
    winner, _ = game.run(agents)
    if winner:
        result_menu.add.label(f'Congratulate {COLOR2STR[winner].lower()} player to win!', max_char=-1, font_size=20)
    else:
        result_menu.add.label(f'DRAW!', max_char=-1, font_size=20)
    result_menu.mainloop(surface)
    
def set_class(config: dict[str, Any], key: str) -> None:
    try:
        class_path = config[key]
        module_path, class_name = class_path.rsplit(".", 1)
        config[key] = getattr(importlib.import_module(module_path), class_name)
    except KeyError:
        pass

def get_object(config: dict[str, Any]) -> object:
    set_class(config, 'type')
    type = config.pop('type')
    return type(**config)
    
def init_agent(agent_type: str, count: int, num_robots: int, with_battery: bool) -> list[BaseAgent]:
    if agent_type == 'dqn':
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
        return [agent]*count
    if agent_type == 'astar':
        agent = AStarAgent(
            colors_map='assets/csv_files/colors_map.csv',
            targets_map='assets/csv_files/targets_map.csv',
            num_robots=num_robots,
            maximum_battery=10 if with_battery else None,
        )
        return [agent]*count
    if agent_type == 'person':
        agent = None
        return [agent]*count
    raise ValueError('No available agent type.')

def selection_placeholder_format(items: list[str]):
    text = ', '.join(items) + ' selected'
    if len(items) <= 1:
        text += '. Too little selected colors.'
    return text

setting_menu.add.range_slider(
    'Required mail', 
    range_values=list(range(1, 21)), 
    default=10,
    onchange=set_required_mail,
    font_size=20,
    range_text_value_enabled=False,
    range_line_height=5,
    slider_thickness=8,
    slider_height_factor=0.5
)
setting_menu.add.dropselect_multiple(
    'Player colors',
    items=[('Red', 'r'),
           ('Blue', 'b'),
           ('Purple', 'p'),
           ('Green', 'gr'),
           ('Pink', 'pi'),
           ('Orange', 'o')],
    default=[0, 1],
    onchange=set_player_colors,
    font_size=20,
    max_selected=4,
    placeholder_selected='{}',
    selection_placeholder_format=selection_placeholder_format,
    selection_box_width = 400,
)
selector_epic = setting_menu.add.dropselect(
    'Number robots per player',
    items=[(str(num), num) for num in range(1, 4)],
    default=0,
    onchange=set_num_robot_per_player,
    font_size=20,
)
setting_menu.add.toggle_switch(
    'With battery', 
    default=False,
    onchange=set_with_battery,
    font_size=20,
    state_color=('#e8e3e7', '#34c0eb'),
)
setting_menu.add.toggle_switch(
    'Random step per turn', 
    default=False,
    onchange=set_random_step_per_turn,
    font_size=20,
    state_color=('#e8e3e7', '#34c0eb'),
)
setting_menu.add.text_input(
    'Max step: ',
    default=1000, 
    onchange=set_max_step,
    input_type=pygame_menu.locals.INPUT_INT,
    font_size=20,
)
for i in range(4):
    setting_menu.add.dropselect(
        f'Player {i+1}', 
        items=[('dqn', 'dqn', i+1), ('astar', 'astar', i+1), ('person', 'person', i+1)], 
        default=0,
        onchange=set_player_type,
        font_size=20)  
    
setting_menu.add.button(
    'OK',
    action=pygame_menu.events.BACK, 
    font_size=20,
)
error_menu.add.label('Please chose more colors for player!' , max_char=-1, font_size=20)
error_menu.add.button('OK', pygame_menu.events.CLOSE)
main_menu.add.button('Play', run_game)
main_menu.add.button('Setting', setting_menu)
main_menu.add.button('Quit', pygame_menu.events.EXIT)
main_menu.mainloop(surface)