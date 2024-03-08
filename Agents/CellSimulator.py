class CellSimulator:

    def __init__(self, y, x, color='w', target=0, robot=None, *,
                 front=None, back=None, left=None, right=None ) -> None:
        
        self.__x = x
        self.__y = y
        self.__color = color
        self.__target = target
        self.robot = robot

        self.front = front
        self.back = back
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f'Cell({self.x}, {self.y})'
    
    #equal and hash dunder method for using a Cell as dictionary's key
    def __eq__(self, cell):
        if isinstance(cell, CellSimulator):
            return self.x == cell.x and self.y == cell.y 
        return NotImplemented

    def __hash__(self):
        return hash((self.x, self.y))    
    
    #less than dunder method for puttting a Cell in priority queue
    def __lt__(self, cell):
        if isinstance(cell, CellSimulator):
            return True
        return NotImplemented

    @property
    def x(self):
        return self.__x
    
    @x.setter
    def x(self, x):
        raise ValueError('Don\'t change x')    
    
    @property
    def y(self):
        return self.__y
    
    @y.setter
    def y(self, y):
        raise ValueError('Don\'t change y')  

    @property
    def color(self):
        return self.__color
    
    @color.setter
    def color(self, color):
        raise ValueError('You can\'t change cell color')    
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, target):
        raise ValueError('You can\'t change cell target')   

    @property
    def neighbors(self):
        return [cell for cell in [self.front, self.back, self.left, self.right] if cell]
    
    @property
    def is_blocked(self):
        if self.color == 'b':
            return len([cell for cell in self.neighbors if (cell.robot and cell.robot.battery <= 30)]) == 1 and self.robot
        if self.color == 'gr':
            return len([cell for cell in self.neighbors if (cell.robot and not cell.robot.mail)]) == 2 and self.robot
        if self.color == 'y':
            return len([cell for cell in self.neighbors if (cell.robot and cell.robot.mail)]) == 2 and self.robot
        return False