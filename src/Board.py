import csv
import queue
from src.Cell import Cell

def heuristic(a: Cell, b: Cell) -> float:
    return abs(a.x - b.x) + abs(a.y - b.y)

class Board:
    def __init__(self, colors_map, targets_map) -> None:
        self.__load_from_file(colors_map, targets_map)
        self.size = len(self.cells[0])

        self.yellow_cells = self.__get_cells_by_color('y')
        self.red_cells = self.__get_cells_by_color('r')
        self.green_cells = self.__get_cells_by_color('gr')
        self.blue_cells = self.__get_cells_by_color('b')
        self.white_cells = self.__get_cells_by_color('w')

    # allow us iterate through cells of boards               
    def __getitem__(self, index):
        return self.cells[index]

    def __get_cells_by_color(self, color):
        return [cell for row_cell in self.cells for cell in row_cell if cell.color == color]
    
    def __load_from_file(self, colors_map, targets_map):

        #two dimension list of Cell
        self.cells = []

        colors_map_file =  open(colors_map, mode ='r')
        targets_map_file = open(targets_map, mode ='r')

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)
        
        #create cells with given colors and targets in csv files
        for i, (color_row, target_row) in enumerate(zip(color_matrix, target_matrix)):
            self.cells.append([])
            for j, (color, target) in enumerate(zip(color_row, target_row)):
                self.cells[-1].append(Cell(i, j, color=color, target=int(target)))

        colors_map_file.close()
        targets_map_file.close()

        #set for each cell its adjacent 
        for i in range(len(self.cells)):
            for j in range(len(self.cells[i])):
                if ((i-1)>=0): self.cells[i][j].front = self.cells[i-1][j]
                if ((i+1)<len(self.cells[i])): self.cells[i][j].back = self.cells[i+1][j]
                if ((j+1)<len(self.cells[i])): self.cells[i][j].right = self.cells[i][j+1]
                if ((j-1)>=0): self.cells[i][j].left = self.cells[i][j-1]

    @property
    def cannot_step(self):
        return [cell for cells in self for cell in cells if (cell.robot or cell.color == 'r' or cell.color == 'y')] 
    
    def a_star_search(self, start, goal):
        open_set = queue.PriorityQueue()
        open_set.put((0, start))
        
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        i=0
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
            #Reverse neighbors list if i is odd, change order putting cell to queue
            #According to that, we don't get cell from queue over one row or column and search over diagonal
            if i%2 == 1 : neighbors.reverse()      
            for next in neighbors:
                new_cost = cost_so_far[current] + 1
                if (next not in cost_so_far or new_cost < cost_so_far[next]) and (next not in self.cannot_step or next == start or next == goal):
                    cost_so_far[next] = new_cost
                    priority = new_cost + heuristic(next, goal)
                    open_set.put((priority, next))
                    came_from[next] = current
            i += 1
        return []
    
    def reset(self):
        for cells in self:
            for cell in cells:
                cell.robot = None

    