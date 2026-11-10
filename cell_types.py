"""Validation for the string states allowed in one automaton."""


def validate_cell_types(names: list[str]) -> tuple[str, ...]:
    if not names:
        raise ValueError("Provide at least one cell type.")
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("Cell types must be nonempty strings.")
    cleaned = tuple(name.strip() for name in names)
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Cell types must be unique.")
    return cleaned
