from typing import Any
import os
from pathlib import Path

import pygame
import pygame_menu
import pygame_menu.events
pygame.init()

from rbgame.game.game import RoboticBoardGame
from rbgame.game.consts import CELL_SIZE, COLOR2STR

def selection_placeholder_format(items: list[str]) -> str:
    """
    A function to specify what display in robot colors selector.

    :param items: list of selected items.
    :return: formated text.
    """
    text = ', '.join(items) + ' selected'
    if len(items) <= 1:
        text += '. Too little selected colors.'
    return text

class RoboticBoardGameMenu:
    """
    A simple menu to custom game parameters and animate the game process with
    these parameters.

    :param agent_fn: Parameter - agent's type, argument - a function with the signature 
    :code:`f(num_robots: int, with_battery: bool) -> BaseAgent`. For example:

    .. code-block::

        RoboticBoardGameMenu(astar=astar_constructor, dqn=dqn_constuctor)

    """
    def __init__(
        self,
        **agent_fn,
    ):
        self.agent_fn = dict(human=lambda num_robots, with_battery: None)
        self.agent_fn.update(agent_fn)
        self.surface = pygame.display.set_mode((15*CELL_SIZE[0], 11*CELL_SIZE[1]))
        pygame.display.set_caption('Robotics Board Game')
        self.main_menu = pygame_menu.Menu(
            'Welcome', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
            theme=pygame_menu.themes.THEME_BLUE,
            onclose=pygame_menu.events.EXIT,
        )
        self.setting_menu = pygame_menu.Menu(
            'Setting', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
            theme=pygame_menu.themes.THEME_BLUE,
        )
        self.result_menu = pygame_menu.Menu(
            'Result', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
            theme=pygame_menu.themes.THEME_BLUE,
            onclose=pygame_menu.events.CLOSE,
        )
        self.error_menu = pygame_menu.Menu(
            'Error', 15*CELL_SIZE[0], 11*CELL_SIZE[1],
            theme=pygame_menu.themes.THEME_BLUE,
            onclose=pygame_menu.events.CLOSE,
        )
        parent_dir = str(Path(__file__).resolve().parents[1])
        self.env_args = {
            'colors_map': os.path.join(parent_dir, 'assets', 'csv_files', 'colors_map.csv'),
            'targets_map': os.path.join(parent_dir, 'assets', 'csv_files', 'targets_map.csv'),
            'required_mail': 10,
            'robot_colors': ['r', 'b'],
            'num_robots_per_player': 1,
            'with_battery': False,
            'random_num_steps': False,
            'max_step': 1000,
            'render_mode': 'human',
        }
        self.player_types = {
            'player1': 'human',
            'player2': 'human',
            'player3': 'human',
            'player4': 'human',
        }
        self.setting_menu.add.range_slider(
            'Required mail', 
            range_values=list(range(1, 21)), 
            default=10,
            onchange=self.__set_required_mail,
            font_size=20,
            range_text_value_enabled=False,
            range_line_height=5,
            slider_thickness=8,
            slider_height_factor=0.5
        )
        self.setting_menu.add.dropselect_multiple(
            'Player colors',
            items=[('Red', 'r'),
                ('Blue', 'b'),
                ('Purple', 'p'),
                ('Green', 'gr'),
                ('Pink', 'pi'),
                ('Orange', 'o')],
            default=[0, 1],
            onchange=self.__set_player_colors,
            font_size=20,
            max_selected=4,
            placeholder_selected='{}',
            selection_placeholder_format=selection_placeholder_format,
            selection_box_width = 400,
        )
        self.setting_menu.add.dropselect(
            'Number robots per player',
            items=[(str(num), num) for num in range(1, 4)],
            default=0,
            onchange=self.__set_num_robots_per_player,
            font_size=20,
        )
        self.setting_menu.add.toggle_switch(
            'With battery', 
            default=False,
            onchange=self.__set_with_battery,
            font_size=20,
            state_color=('#e8e3e7', '#34c0eb'),
        )
        self.setting_menu.add.toggle_switch(
            'Random step per turn', 
            default=False,
            onchange=self.__set_random_num_step,
            font_size=20,
            state_color=('#e8e3e7', '#34c0eb'),
        )
        self.setting_menu.add.text_input(
            'Max step: ',
            default=1000, 
            onchange=self.__set_max_step,
            input_type=pygame_menu.locals.INPUT_INT,
            font_size=20,
        )
        for i in range(4):
            self.setting_menu.add.dropselect(
                f'Player {i+1}', 
                items=[(agent_type, agent_type, i+1) for agent_type in self.agent_fn.keys()], 
                default=0,
                onchange=self.__set_player_type,
                font_size=20,
                )  
            
        self.setting_menu.add.button(
            'OK',
            action=pygame_menu.events.BACK, 
            font_size=20,
        )
        self.error_menu.add.label('Please chose more colors for player!' , max_char=-1, font_size=20)
        self.error_menu.add.button('OK', pygame_menu.events.CLOSE)
        self.main_menu.add.button('Play', self.__run_game)
        self.main_menu.add.button('Setting', self.setting_menu)
        self.main_menu.add.button('Quit', pygame_menu.events.EXIT)
        self.main_menu.mainloop(self.surface)
    
    def __set_required_mail(self, required_mail: int) -> None:
        self.env_args['required_mail'] = required_mail

    def __set_player_colors(self, items: tuple[Any, list[int]]) -> None:
        item_values, _ = items
        self.env_args['robot_colors'] = [item_value[1] for item_value in item_values]

    def __set_num_robots_per_player(self, items: tuple[Any, int], num_robots_per_player: int) -> None:
        self.env_args['num_robots_per_player'] = num_robots_per_player

    def __set_max_step(self, max_step: int) -> None:
        self.env_args['max_step'] = max_step

    def __set_with_battery(self, with_battery: bool) -> None:
        self.env_args['with_battery'] = with_battery

    def __set_random_num_step(self, random_num_steps: bool) -> None:
        self.env_args['random_num_steps'] = random_num_steps
    
    def __set_player_type(self, items: tuple[Any, int], player_type: int, player_index: int) -> None:
        self.player_types[f'player{player_index}'] = player_type

    def __run_game(self) -> None:
        if len(self.env_args['robot_colors']) <= 1:
            self.error_menu.enable()
            self.error_menu.mainloop(self.surface)
            return
        agents = []
        for i, _ in enumerate(self.env_args['robot_colors']):
            agent_type = self.player_types[f'player{i+1}']
            agents.extend(self.env_args['num_robots_per_player']*
                [self.agent_fn[agent_type](
                    self.env_args['num_robots_per_player']*len(self.env_args['robot_colors']),
                    self.env_args['with_battery'],
                )])
        game = RoboticBoardGame(**self.env_args)
        winner, _ = game.run(agents)
        self.result_menu.enable()
        self.result_menu.clear()
        if winner:
            self.result_menu.add.label(f'Congratulate {COLOR2STR[winner].lower()} player to win!', max_char=-1, font_size=20)
        else:
            self.result_menu.add.label(f'DRAW!', max_char=-1, font_size=20)
        self.result_menu.add.button('OK', pygame_menu.events.CLOSE)
        self.result_menu.mainloop(self.surface)