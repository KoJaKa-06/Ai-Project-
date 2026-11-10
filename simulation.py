"""Synchronous updates using eight neighbors and finite, non-wrapping edges."""

from collections import Counter
from typing import Iterable

from automaton import Automaton
from rules import Rule, next_cell_type


def count_neighbors(matrix: list[list[str]], row: int, column: int) -> dict[str, int]:
    """Count surrounding cells, excluding the center and out-of-bounds positions."""
    counts = Counter()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, column + dc
            if 0 <= nr < len(matrix) and 0 <= nc < len(matrix[nr]):
                counts[matrix[nr][nc]] += 1
    return dict(counts)


def step(world: Automaton, rules: Iterable[Rule]) -> None:
    """Advance one generation, replacing the matrix only after all cells are evaluated."""
    rules = tuple(rules)
    for rule in rules:
        rule.validate_types(world.cell_types)
    current = world.matrix
    following = [
        [next_cell_type(current[row][column], count_neighbors(current, row, column), rules)
         for column in range(world.columns)]
        for row in range(world.rows)
    ]
    world.matrix = following
