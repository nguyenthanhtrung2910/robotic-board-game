from __future__ import annotations
import math
import random
import csv
import queue
import typing

import numpy as np

from src.game.game_components import Action
from src.consts import *

class Vertex:

    def __init__(self,
                 y: int,
                 x: int,
                 color: str = 'w',
                 target: int = 0,
                 robot: Robot | None = None,
                 mail: int = 0,
                 *,
                 front: 'Vertex | None' = None,
                 back: 'Vertex | None' = None,
                 left: 'Vertex | None' = None,
                 right: 'Vertex | None' = None) -> None:

        self.__x = x
        self.__y = y
        self.__color = color
        self.__target = target
        self.robot = robot
        self.mail = mail

        self.front = front
        self.back = back
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f'Vertex({self.x}, {self.y})'

    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, vertex: object) -> bool:
        if isinstance(vertex, Vertex):
            return self.x == vertex.x and self.y == vertex.y
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    #less than dunder method for puttting a Cell in priority queue
    def __lt__(self, vertex: object) -> bool:
        if isinstance(vertex, Vertex):
            return True
        return NotImplemented

    @property
    def x(self) -> int:
        return self.__x

    @x.setter
    def x(self, x: int) -> None:
        raise ValueError('Don\'t change x')

    @property
    def y(self) -> int:
        return self.__y

    @y.setter
    def y(self, y: int) -> None:
        raise ValueError('Don\'t change y')

    @property
    def color(self) -> str:
        return self.__color

    @color.setter
    def color(self, color: str) -> None:
        raise ValueError('You can\'t change cell color')

    @property
    def target(self) -> int:
        return self.__target

    @target.setter
    def target(self, target: int) -> None:
        raise ValueError('You can\'t change cell target')

    @property
    def neighbors(self) -> list['Vertex']:
        return [
            vertex for vertex in [self.front, self.back, self.left, self.right]
            if vertex
        ]

    @property
    def is_blocked(self) -> bool:
        if self.color == 'b':
            return len([
                vertex for vertex in self.neighbors
                if (vertex.robot and vertex.robot.battery <= 30)
            ]) == 1 and self.robot is not None
        if self.color == 'gr':
            return len([
                vertex for vertex in self.neighbors
                if (vertex.robot and not vertex.robot.mail)
            ]) == 2 and self.robot is not None
        if self.color == 'y':
            return len([
                vertex
                for vertex in self.neighbors if (vertex.robot and vertex.robot.mail)
            ]) == 2 and self.robot is not None
        return False

    def generate_mail(self) -> None:
        self.mail = random.choice(range(1, 10))

class Graph:

    def __init__(self, colors_map: str, targets_map: str) -> None:
        self.__load_from_file(colors_map, targets_map)
        self.size = len(self.vertices[0])

        self.yellow_vertices = self.__get_vertices_by_color('y')
        self.red_vertices = self.__get_vertices_by_color('r')
        self.green_vertices = self.__get_vertices_by_color('gr')
        self.blue_vertices = self.__get_vertices_by_color('b')
        self.white_vertecies = self.__get_vertices_by_color('w')

    # allow us access cell by coordinate
    def __getitem__(self, coordinate: tuple[int,
                                            int]) -> Vertex:
        return self.vertices[coordinate[1]][coordinate[0]]

    def __get_vertices_by_color(self,
                             color: str) -> list[Vertex]:
        return [
            vertex for row_vertex in self.vertices for vertex in row_vertex
            if vertex.color == color
        ]

    def __load_from_file(self, colors_map: str, targets_map: str) -> None:

        #two dimension list of Cell
        self.vertices: list[list[Vertex]] = []

        colors_map_file = open(colors_map, mode='r', encoding="utf-8")
        targets_map_file = open(targets_map, mode='r', encoding="utf-8")

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)

        #create cells with given colors and targets in csv files
        for i, (color_row,
                target_row) in enumerate(zip(color_matrix, target_matrix)):
            self.vertices.append([])
            for j, (color, target) in enumerate(zip(color_row, target_row)):
                self.vertices[-1].append(
                    Vertex(i,
                                j,
                                color=color,
                                target=int(target)))

        colors_map_file.close()
        targets_map_file.close()

        #set for each cell its adjacent
        for i, _ in enumerate(self.vertices):
            for j, _ in enumerate(self.vertices[i]):
                if (i - 1) >= 0:
                    self.vertices[i][j].front = self.vertices[i - 1][j]
                if (i + 1) < len(self.vertices[i]):
                    self.vertices[i][j].back = self.vertices[i + 1][j]
                if (j + 1) < len(self.vertices[i]):
                    self.vertices[i][j].right = self.vertices[i][j + 1]
                if (j - 1) >= 0:
                    self.vertices[i][j].left = self.vertices[i][j - 1]

    @property
    def cannot_step(self) -> list[Vertex]:
        return [
            vertex for vertices in self.vertices for vertex in vertices
            if (vertex.robot or vertex.color == 'r' or vertex.color == 'y'
                or vertex.color == 'gr')
        ]

    @staticmethod
    def heuristic(a: Vertex,
                  b: Vertex) -> float:
        return abs(a.x - b.x) + abs(a.y - b.y)

    def reset(self) -> None:
        for vertices in self.vertices:
            for vertex in vertices:
                vertex.robot = None
                vertex.mail = 0

    def a_star_search(
            self, start: Vertex,
            goal: Vertex) -> list[Vertex]:
        open_set: queue.PriorityQueue = queue.PriorityQueue()
        open_set.put((0, start))

        came_from: dict[Vertex,
                        Vertex | None] = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        i = 0
        while not open_set.empty():
            current = open_set.get()[1]

            if current == goal:
                path = []
                while current != start:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            neighbors = current.neighbors
            #Reverse neighbors list if i is odd,
            #change order putting cell to queue
            #According to that, we don't get cell from queue over
            #one row or column and search over diagonal
            if i % 2 == 1:
                neighbors.reverse()
            for next_vertex in neighbors:
                new_cost = cost_so_far[current] + 1
                if (next_vertex not in cost_so_far
                        or new_cost < cost_so_far[next_vertex]) and (
                            next_vertex not in self.cannot_step
                            or next_vertex == start or next_vertex == goal):
                    cost_so_far[next_vertex] = new_cost
                    priority = new_cost + self.heuristic(next_vertex, goal)
                    open_set.put((priority, next_vertex))
                    came_from[next_vertex] = current
            i += 1
        return []

class Robot:

    def __init__(self,
                 pos: Vertex,
                 index: int,
                 color: str,
                 mail: int = 0,
                 count_mail: int = 0,
                 battery: int = MAXIMUM_ROBOT_BATTERY):
        self.pos = pos
        self.pos.robot = self
        self.index = index
        self.color = color
        self.mail = mail
        self.count_mail = count_mail
        self.battery = battery

    @property
    def is_charged(self) -> bool:
        return self.pos.color == 'b'

    def move_up(self) -> bool:
        if self.battery:
            if self.is_legal_moves(Action.GO_AHEAD):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail()
                self.pos = self.pos.front
                self.pos.robot = self
                self.battery -= 1
                self.pick_up()
                self.drop_off()
                return True
        return False

    def move_down(self) -> bool:
        if self.battery:
            if self.is_legal_moves(Action.GO_BACK):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail()
                self.pos = self.pos.back
                self.pos.robot = self
                self.battery -= 1
                self.pick_up()
                self.drop_off()
                return True
        return False

    def move_right(self) -> bool:
        if self.battery:
            if self.is_legal_moves(Action.TURN_RIGHT):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail()
                self.pos = self.pos.right
                self.pos.robot = self
                self.battery -= 1
                self.pick_up()
                self.drop_off()
                return True
        return False

    def move_left(self) -> bool:
        if self.battery:
            if self.is_legal_moves(Action.TURN_LEFT):
                self.pos.robot = None
                if self.pos.color == 'gr':
                    self.pos.generate_mail()
                self.pos = self.pos.left
                self.pos.robot = self
                self.battery -= 1
                self.pick_up()
                self.drop_off()
                return True
        return False

    def pick_up(self) -> bool:
        if not self.mail and self.pos.color == 'gr':
            self.mail = self.pos.mail
            return True
        return False

    def drop_off(self) -> bool | int:
        if self.mail and self.pos.color == 'y':
            deliveried_mail = self.mail
            self.mail = 0
            self.count_mail += 1
            return deliveried_mail
        return False
    
    def charge(self) -> None:
        self.battery += BATERRY_UP_PER_STEP
        if self.battery > MAXIMUM_ROBOT_BATTERY:
            self.battery = MAXIMUM_ROBOT_BATTERY
    
    def reset(self, pos: Vertex) -> None:
        self.pos = pos
        self.pos.robot = self
        self.mail = 0
        self.count_mail = 0
        self.battery = MAXIMUM_ROBOT_BATTERY
    
    def is_legal_moves(self, action: int) -> bool:
        if action == Action.DO_NOTHING:
            return True
        
        if action == Action.GO_AHEAD:
            if self.pos.front:
                if self.pos.front.color != 'r' and self.pos.front.robot is None and (
                    self.pos.front.color != 'y' or (self.mail != 0 and self.pos.front.target == self.mail)) and (
                    self.pos.front.color != 'gr' or self.mail == 0):
                    return True
            
        if action == Action.GO_BACK:
            if self.pos.back:
                if self.pos.back.color != 'r' and self.pos.back.robot is None and (
                    self.pos.back.color != 'y' or (self.mail != 0 and self.pos.back.target == self.mail)) and (
                    self.pos.back.color != 'gr' or self.mail == 0):
                    return True
                
        if action == Action.TURN_LEFT:
            if self.pos.left:
                if self.pos.left.color != 'r' and self.pos.left.robot is None and (
                    self.pos.left.color != 'y' or (self.mail != 0 and self.pos.left.target == self.mail)) and (
                    self.pos.left.color != 'gr' or self.mail == 0):
                    return True
                
        if action == Action.TURN_RIGHT:
            if self.pos.right:
                if self.pos.right.color != 'r' and self.pos.right.robot is None and (
                    self.pos.right.color != 'y' or (self.mail != 0 and self.pos.right.target == self.mail)) and (
                    self.pos.right.color != 'gr' or self.mail == 0):
                    return True
                
        return False

    def get_destination(
        self,
        board: Graph,
        blocked: list[Vertex] = []
    ) -> Vertex:
        if self.battery <= 30:
            return min(
                [cell for cell in board.blue_vertices if cell not in blocked],
                key=lambda blue_cell: Graph.heuristic(
                    self.pos, blue_cell))
        else:
            if self.mail:
                for yellow_cell in board.yellow_vertices:
                    if yellow_cell.target == self.mail:
                        return yellow_cell
            else:
                return min([
                    cell for cell in board.green_vertices if cell not in blocked
                ],
                           key=lambda green_cell: Graph.
                           heuristic(self.pos, green_cell))
        return self.pos
    
class Simulator:

    def __init__(self, 
                 colors_map: str,
                 targets_map: str,
                 state: dict[str, list[dict[str, typing.Any]] | list[int]]) -> None:

        self.graph = Graph(colors_map=colors_map, targets_map=targets_map)
        self.robots: dict[str, list[Robot]] = {}
        for robot_state in state['robots_state']:
            self.robots[robot_state['color']] = []
        for robot_state in state['robots_state']:
            robot = Robot(
                self.graph[robot_state['pos'][0],
                           robot_state['pos'][1]], robot_state['index'],
                robot_state['color'], robot_state['mail'],
                robot_state['count_mail'], robot_state['battery'])
            self.robots[robot.color].append(robot)

        for green_cell, mail_number in zip(self.graph.green_vertices,
                                           state['generated_mails']):
            green_cell.mail = mail_number

    def sum_count_mail(self, color: str) -> int:
        return sum([robot.count_mail for robot in self.robots[color]])

    def update(self, state: dict[str,
                                 list[dict[str, typing.Any]] | list[int]]) -> None:
        for robot_state in state['robots_state']:
            robot: Robot = self.robots[
                robot_state['color']][robot_state['index'] - 1]
            robot.pos.robot = None
            robot.pos = self.graph[robot_state['pos'][0],
                                   robot_state['pos'][1]]
            robot.pos.robot = robot
            robot.mail = robot_state['mail']
            robot.count_mail = robot_state['count_mail']
            robot.battery = robot_state['battery']

        for green_cell, mail_number in zip(self.graph.green_vertices,
                                           state['generated_mails']):
            green_cell.mail = mail_number

    def reset(self, state: dict[str,
                                list[dict[str, typing.Any]] | list[int]]) -> None:
        self.graph.reset()

        for robot_state in state['robots_state']:
            robot: Robot = self.robots[
                robot_state['color']][robot_state['index'] - 1]
            robot.reset(self.graph[robot_state['pos'][0], robot_state['pos'][1]])

        for green_cell, mail_number in zip(self.graph.green_vertices,
                                           state['generated_mails']):
            green_cell.mail = mail_number

class AStarAgent:

    def __init__(self, 
                 color: str,
                 colors_map: str,
                 targets_map: str,
                 state) -> None:

        self.color = color
        self.simulator = Simulator(colors_map, targets_map, state)
        self.dests: list[Vertex] = []
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(self.simulator.graph))

    def __get_action_for_one_robot(self, robot: Robot,
                                   board: Graph) -> int:
        if robot.is_charged:
            if robot.battery < 70:
                return 0

        if robot.pos is self.dests[robot.index - 1]:
            self.dests[robot.index - 1] = robot.get_destination(board)

        # when many other robot wait for queue to destination, go to other destination or don't move
        # we want avoid draw when all players don't want to move

        if self.dests[robot.index -
                      1].is_blocked and robot.pos not in self.dests[
                          robot.index - 1].neighbors:
            if self.dests[robot.index - 1].color == 'y':
                return 0
            if self.dests[robot.index - 1].color == 'b':
                if all([cell.is_blocked for cell in board.blue_vertices]):
                    return 0
                self.dests[robot.index - 1] = robot.get_destination(
                    board,
                    [cell for cell in board.blue_vertices if cell.is_blocked])
            if self.dests[robot.index - 1].color == 'gr':
                if all([cell.is_blocked for cell in board.green_vertices]):
                    return 0
                self.dests[robot.index - 1] = robot.get_destination(
                    board,
                    [cell for cell in board.green_vertices if cell.is_blocked])

        #build the path
        path = board.a_star_search(robot.pos, self.dests[robot.index - 1])

        if len(path) != 0:
            next = path[0]

            #get the action
            if next is robot.pos.front:
                action = 1
            if next is robot.pos.back:
                action = 2
            if next is robot.pos.left:
                action = 3
            if next is robot.pos.right:
                action = 4

            #simulation
            if not next.robot:
                robot.pos.robot = None
                if robot.pos.color == 'gr':
                    robot.pos.generate_mail()
                robot.pos = next
                robot.pos.robot = robot
                #rows below not necessary because agent control next robot and don't need 
                #to known about battery and mail of the previous robot
                robot.battery -= 1
                robot.pick_up()
                robot.drop_off()

                #charge robot in blue cells
                for blue_cell in board.blue_vertices:
                    if blue_cell.robot:
                        if blue_cell.robot is not robot:
                            blue_cell.robot.charge()

            return action

        return 0

    def get_action(self, state) -> int:
        #update the game state for simulator
        self.simulator.update(state)

        #simulation
        action = [
            self.__get_action_for_one_robot(robot, self.simulator.graph)
            for robot in self.simulator.robots[self.color]
        ] + [0]

        number_robots_per_agent = len(list(self.simulator.robots.values())[0])
        action = np.ravel_multi_index(action, [5]*number_robots_per_agent+[math.factorial(number_robots_per_agent)])
        
        return action

    def reset(self, state) -> None:
        self.simulator.reset(state)
        self.dests = []
        for robot in self.simulator.robots[self.color]:
            self.dests.append(robot.get_destination(self.simulator.graph))
