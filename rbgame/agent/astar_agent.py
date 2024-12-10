from __future__ import annotations
import random
import csv
import queue

import numpy as np

from rbgame.agent.base_agent import BaseAgent

class Vertex:
    """
    Similar to :py:class:`Cell <rbgame.game.components.Cell>`.

    :param x: The abscissa in the graph. The coordinate origin is at the top left point, positive direction from left to right.
    :param y: The ordinate in the graph. The coordinate origin is at the top left point, positive direction from top to bottom.
    :param color: The color of the vertex. Possible colors are ``'w'`` - white, ``'b'`` - blue,  ``'r'`` - red, ``'y'`` - yellow, ``'gr'`` - green, ``'g'`` - gray.
    :param target: The target of this vertex. 
    :param robot: The located in this vertex robot.
    :param mail: Generated mail in this vertex.
    :param front: The front vertex of this vertex.
    :param back: The back vertex of this vertex.
    :param left: The left vertex of this vertex.
    :param right: The right vertex of this vertex.
    """
    def __init__(
        self,
        y: int,
        x: int,
        color: str = 'w',
        target: int = 0,
        robot: VRobot | None = None,
        mail: int = 0,
        *,
        front: 'Vertex | None' = None,
        back: 'Vertex | None' = None,
        left: 'Vertex | None' = None,
        right: 'Vertex | None' = None
    ) -> None:

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

    # equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, vertex: object) -> bool:
        if isinstance(vertex, Vertex):
            return self.x == vertex.x and self.y == vertex.y
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    # less than dunder method for puttting a Cell in priority queue
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
        raise ValueError('You can\'t change vertex color')

    @property
    def target(self) -> int:
        return self.__target

    @target.setter
    def target(self, target: int) -> None:
        raise ValueError('You can\'t change vertex target')

    @property
    def neighbors(self) -> list['Vertex']:
        """
        Returns neighboring verties of this vertex.
        """
        return [
            vertex for vertex in [self.front, self.back, self.left, self.right]
            if vertex
        ]

    @property
    def is_blocked(self) -> bool:
        """
        Vertex is blocked (robot shouldn't go there) if it has too much robots 
        waiting to go to this vertex.
        """
        # blue vertex with robot in this and other robot is waiting
        if self.color == 'b':
            return len([
                vertex for vertex in self.neighbors
                if (vertex.robot and vertex.robot.battery <= 30)
            ]) == 1 and self.robot is not None
        # green vertex with robot in this and two other robots is waiting
        if self.color == 'gr':
            return len([
                vertex for vertex in self.neighbors
                if (vertex.robot and not vertex.robot.mail)
            ]) == 2 and self.robot is not None
        # yellow vertex with robot in this and two other robots is waiting
        if self.color == 'y':
            return len([
                vertex
                for vertex in self.neighbors if (vertex.robot and vertex.robot.mail)
            ]) == 2 and self.robot is not None
        return False

class Graph:
    """
    Similar to :py:class:`Board <rbgame.game.components.Board>`. It is set of :py:class:`Vertex`.

    :param colors_map: csv file name for color map. 
                       Each element define :py:attr:`color` of each :py:class:`Vertex`.
    :param targets_map: csv file name for target map. 
                        Each element define :py:attr:`target` of each :py:class:`Vertex`. 
    """

    def __init__(self, colors_map: str, targets_map: str) -> None:
        self.__load_from_file(colors_map, targets_map)
        self.size = len(self.vertices[0])

        self.yellow_vertices = self.__get_vertices_by_color('y')
        self.red_vertices = self.__get_vertices_by_color('r')
        self.green_vertices = self.__get_vertices_by_color('gr')
        self.blue_vertices = self.__get_vertices_by_color('b')
        self.white_vertecies = self.__get_vertices_by_color('w')

    # allow us access vertex by coordinate
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

        # two dimension list of Cell
        self.vertices: list[list[Vertex]] = []

        colors_map_file = open(colors_map, mode='r', encoding="utf-8")
        targets_map_file = open(targets_map, mode='r', encoding="utf-8")

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)

        # create vertices with given colors and targets in csv files
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

        # set for each vertex its adjacent
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
                or vertex.color == 'gr' or vertex.color == 'b')
        ]

    @staticmethod
    def heuristic(a: Vertex,
                  b: Vertex) -> float:
        return abs(a.x - b.x) + abs(a.y - b.y)

    def a_star_search(
            self, start: Vertex,
            goal: Vertex) -> list[Vertex]:
        """
        A* search for shortest path from :code:`start` to :code:`goal`
        . About algorithm, go `here <https://en.wikipedia.org/wiki/A*_search_algorithm>`_.

        :param start: start vertex.
        :param goal: end vertex.
        :return: Path from start vertex to end vertex. Start vertex doesn't includes in found path. 
                 Return to empty :py:class:`list` if path not found.
        """
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
            # reverse neighbors list if i is odd, change order putting vertex to queue
            # according to that, we don't get vertex from queue over one row or column and search over diagonal
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

class VRobot:
    """
    Similar to :py:class:`Robot <rbgame.game.components.Robot>`.

    :param pos: Current position of the robot.
    :param mail: The mail that robot are carring.
    :param battery: The battery.
    """
    def __init__(
        self,
        pos: Vertex,
        battery: int = 0,
        mail: int = 0,
    ) -> None:
        self.pos = pos
        self.pos.robot = self
        self.battery = battery
        self.mail = mail
        self.dest = None

    @property
    def is_charged(self) -> bool:
        """
        Robot is charging or not.
        """
        return self.pos.color == 'b'
    
    def set_destination(
        self,
        board: Graph,
        blocked: list[Vertex] = []
    ) -> None:
        """
        Set destination for robot base on its state.

        :param board: A graph to get destination from it.
        :param blocked: List of blocked vertices that destination shouldn't be in.
        """
        if self.battery <= 4:
            self.dest = min(
                [vertex for vertex in board.blue_vertices if vertex not in blocked],
                key=lambda blue_vertex: Graph.heuristic(
                    self.pos, blue_vertex))
        else:
            if self.mail:
                self.dest = [yellow_vertex for yellow_vertex in board.yellow_vertices if yellow_vertex.target == self.mail][0]
            else:
                self.dest = min([
                    vertex for vertex in board.green_vertices if vertex not in blocked
                ],
                           key=lambda green_vertex: Graph.
                           heuristic(self.pos, green_vertex))
    
class AStarAgent(BaseAgent):
    """
    A controller for single robot, using A* star search shortest path.
    See algorithm in :doc:`../../../astar_agent_doc`.

    :param colors_map: Colors map of the graph.
    :param targets_map: Target map of the graph.
    :param num_robots: Number of robots on the game board.
    :param maximum_battery: Maximum battery for robot.
    """

    def __init__(self,
                 colors_map: str,
                 targets_map: str,
                 num_robots: int,
                 maximum_battery: int|None = None) -> None:
        self.graph = Graph(colors_map=colors_map, targets_map=targets_map)
        self.num_robots = num_robots
        robot_vertices_init = random.sample(self.graph.white_vertecies, k=self.num_robots)
        self.robots = [VRobot(robot_vertices_init[i], 10) for i in range(self.num_robots)]
        self.max_values_for_robot_attrs = [self.graph.size-1, self.graph.size-1, len(self.graph.yellow_vertices)]
        if maximum_battery is not None:
            self.max_values_for_robot_attrs.append(maximum_battery)
    
    def __load_state_from_obs(self, obs: np.ndarray) -> None:
        robot_states = np.split(obs, self.num_robots)
        for robot, robot_state in zip(self.robots, robot_states):
            robot.pos.robot = None
            robot.pos = self.graph[int(robot_state[0]*self.max_values_for_robot_attrs[0]), 
                                   int(robot_state[1]*self.max_values_for_robot_attrs[1])]
            robot.mail = int(robot_state[2]*self.max_values_for_robot_attrs[2])
            if len(self.max_values_for_robot_attrs) > 3:
                robot.battery = int(robot_state[3]*self.max_values_for_robot_attrs[3])
        for robot in self.robots:
            robot.pos.robot = robot

    @staticmethod
    def __apply_action_mask(action: int, action_mask: np.ndarray) -> int:
        if not any(action_mask): 
            return action
        return action if action_mask[action] else random.choice([act for act in range(5) if action_mask[act]])
        
    def get_action(self, obs: dict[str, np.ndarray]) -> int:        
        mask = obs.get('action_mask', np.array([1]*5, dtype = np.uint8))
        obs = obs['observation']
        self.__load_state_from_obs(obs)
        acting_robot = self.robots[0]
        if acting_robot.is_charged and acting_robot.battery < 8:
            return self.__apply_action_mask(0, mask)
        
        acting_robot.set_destination(self.graph)
        # when many other robot wait for queue to destination, go to other destination or don't move
        # we want avoid draw when all players don't want to move
        if acting_robot.dest.is_blocked and acting_robot.pos not in acting_robot.dest.neighbors:
            if acting_robot.dest.color == 'y':
                return self.__apply_action_mask(0, mask)
            if acting_robot.dest.color == 'b':
                if all([vertex.is_blocked for vertex in self.graph.blue_vertices]):
                    return self.__apply_action_mask(0, mask)
                acting_robot.set_destination(self.graph, [vertex for vertex in self.graph.blue_vertices if vertex.is_blocked])
            if acting_robot.dest.color == 'gr':
                if all([vertex.is_blocked for vertex in self.graph.green_vertices]):
                    return self.__apply_action_mask(0, mask)
                acting_robot.set_destination(self.graph, [vertex for vertex in self.graph.green_vertices if vertex.is_blocked])

        # build the path
        path = self.graph.a_star_search(acting_robot.pos, acting_robot.dest)
        if len(path) != 0:
            next = path[0]
            if next is acting_robot.pos.front:
                action = 1
            elif next is acting_robot.pos.back:
                action = 2
            elif next is acting_robot.pos.left:
                action = 3
            elif next is acting_robot.pos.right:
                action = 4
            return action if mask[action] else self.__apply_action_mask(0, mask)
        return self.__apply_action_mask(0, mask)