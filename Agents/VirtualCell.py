import random
from Agents import VirtualRobot


class VirtualCell:

    def __init__(self,
                 y: int,
                 x: int,
                 color: str = 'w',
                 target: int = 0,
                 robot: VirtualRobot.VirtualRobot | None = None,
                 mail: int = 0,
                 *,
                 front: 'VirtualCell | None' = None,
                 back: 'VirtualCell | None' = None,
                 left: 'VirtualCell | None' = None,
                 right: 'VirtualCell | None' = None) -> None:

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
        return f'Cell({self.x}, {self.y})'

    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, cell: object) -> bool:
        if isinstance(cell, VirtualCell):
            return self.x == cell.x and self.y == cell.y
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    #less than dunder method for puttting a Cell in priority queue
    def __lt__(self, cell: object) -> bool:
        if isinstance(cell, VirtualCell):
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
    def neighbors(self) -> list['VirtualCell']:
        return [
            cell for cell in [self.front, self.back, self.left, self.right]
            if cell
        ]

    @property
    def is_blocked(self) -> bool:
        if self.color == 'b':
            return len([
                cell for cell in self.neighbors
                if (cell.robot and cell.robot.battery <= 30)
            ]) == 1 and self.robot is not None
        if self.color == 'gr':
            return len([
                cell for cell in self.neighbors
                if (cell.robot and not cell.robot.mail)
            ]) == 2 and self.robot is not None
        if self.color == 'y':
            return len([
                cell
                for cell in self.neighbors if (cell.robot and cell.robot.mail)
            ]) == 2 and self.robot is not None
        return False

    def generate_mail(self) -> None:
        self.mail = random.choice(range(1, 10))
