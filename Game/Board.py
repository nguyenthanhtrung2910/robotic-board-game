import csv

from Game import Cell


class Board:

    def __init__(self, colors_map: str, targets_map: str) -> None:
        self.__load_from_file(colors_map, targets_map)
        self.size = len(self.cells[0])

        self.yellow_cells = self.__get_cells_by_color('y')
        self.red_cells = self.__get_cells_by_color('r')
        self.green_cells = self.__get_cells_by_color('gr')
        self.blue_cells = self.__get_cells_by_color('b')
        self.white_cells = self.__get_cells_by_color('w')

    # allow us access cell by coordinate
    def __getitem__(self, coordinate: tuple[int, int]) -> Cell.Cell:
        return self.cells[coordinate[1]][coordinate[0]]

    def __get_cells_by_color(self, color: str) -> list[Cell.Cell]:
        return [
            cell for row_cell in self.cells for cell in row_cell
            if cell.color == color
        ]

    def __load_from_file(self, colors_map: str, targets_map: str) -> None:

        #two dimension list of Cell
        self.cells: list[list[Cell.Cell]] = []

        colors_map_file = open(colors_map, mode='r', encoding="utf-8")
        targets_map_file = open(targets_map, mode='r', encoding="utf-8")

        color_matrix = csv.reader(colors_map_file)
        target_matrix = csv.reader(targets_map_file)

        #create cells with given colors and targets in csv files
        for i, (color_row,
                target_row) in enumerate(zip(color_matrix, target_matrix)):
            self.cells.append([])
            for j, (color, target) in enumerate(zip(color_row, target_row)):
                self.cells[-1].append(
                    Cell.Cell(i, j, color=color, target=int(target)))

        colors_map_file.close()
        targets_map_file.close()

        #set for each cell its adjacent
        for i, _ in enumerate(self.cells):
            for j, _ in enumerate(self.cells[i]):
                if (i - 1) >= 0:
                    self.cells[i][j].front = self.cells[i - 1][j]
                if (i + 1) < len(self.cells[i]):
                    self.cells[i][j].back = self.cells[i + 1][j]
                if (j + 1) < len(self.cells[i]):
                    self.cells[i][j].right = self.cells[i][j + 1]
                if (j - 1) >= 0:
                    self.cells[i][j].left = self.cells[i][j - 1]

    @property
    def cannot_step(self) -> list[Cell.Cell]:
        return [
            cell for cells in self.cells for cell in cells
            if (cell.robot or cell.color == 'r' or cell.color == 'y')
        ]

    def reset(self) -> None:
        for cells in self.cells:
            for cell in cells:
                cell.robot = None
