"""World initialization; no parser or evolution engine yet."""

from cell_types import validate_cell_types


class Automaton:
    def __init__(self, rows: int, columns: int, cell_types: list[str], default_type: str):
        if type(rows) is not int or type(columns) is not int:
            raise ValueError("Rows and columns must be integers.")
        if rows <= 0 or columns <= 0:
            raise ValueError("Rows and columns must be positive.")
        self.rows = rows
        self.columns = columns
        self.cell_types = validate_cell_types(cell_types)
        self._validate_type(default_type)
        self.matrix = [[default_type for _ in range(columns)] for _ in range(rows)]

    def _validate_type(self, cell_type: str) -> None:
        if cell_type not in self.cell_types:
            raise ValueError(f"Unknown cell type: {cell_type!r}")

    def set_cell(self, row: int, column: int, cell_type: str) -> None:
        if type(row) is not int or type(column) is not int:
            raise ValueError("Cell coordinates must be integers.")
        if not (0 <= row < self.rows and 0 <= column < self.columns):
            raise IndexError("Cell coordinates are outside the matrix.")
        self._validate_type(cell_type)
        self.matrix[row][column] = cell_type

    def snapshot(self) -> list[list[str]]:
        """Return a copy so callers can retain an independent state."""
        return [row.copy() for row in self.matrix]
