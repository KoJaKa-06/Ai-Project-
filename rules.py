"""Validated transition rules and JSON conversion; no natural-language parser."""

from dataclasses import dataclass
import json
import operator as comparisons
from pathlib import Path
from typing import Iterable, Mapping

from cell_types import validate_cell_types


OPERATORS = {
    "==": comparisons.eq,
    "!=": comparisons.ne,
    "<": comparisons.lt,
    "<=": comparisons.le,
    ">": comparisons.gt,
    ">=": comparisons.ge,
}


@dataclass(frozen=True)
class Rule:
    source: str
    target: str
    neighbor_type: str | None = None
    operator: str | None = None
    count: int | None = None

    def __post_init__(self) -> None:
        for name in (self.source, self.target):
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Rule source and target must be nonempty strings.")
        condition = (self.neighbor_type, self.operator, self.count)
        if all(value is None for value in condition):
            return
        if any(value is None for value in condition):
            raise ValueError("A condition requires neighbor_type, operator and count together.")
        if not isinstance(self.neighbor_type, str) or not self.neighbor_type.strip():
            raise ValueError("neighbor_type must be a nonempty string.")
        if not isinstance(self.operator, str) or self.operator not in OPERATORS:
            raise ValueError(f"Unsupported operator: {self.operator!r}")
        if type(self.count) is not int or self.count < 0:
            raise ValueError("count must be a nonnegative integer.")

    def validate_types(self, cell_types: Iterable[str]) -> None:
        allowed = validate_cell_types(list(cell_types))
        names = [self.source, self.target]
        if self.neighbor_type is not None:
            names.append(self.neighbor_type)
        for name in names:
            if name not in allowed:
                raise ValueError(f"Unknown rule cell type: {name!r}")

    def matches(self, current_type: str, neighbor_counts: Mapping[str, int]) -> bool:
        """Counts come from the old generation; missing types have count zero."""
        if current_type != self.source:
            return False
        if self.neighbor_type is None:
            return True
        actual = neighbor_counts.get(self.neighbor_type, 0)
        if type(actual) is not int or actual < 0:
            raise ValueError("Neighbor counts must be nonnegative integers.")
        return OPERATORS[self.operator](actual, self.count)

    def to_dict(self) -> dict:
        result = {"source": self.source, "target": self.target}
        if self.neighbor_type is not None:
            result.update(neighbor_type=self.neighbor_type, operator=self.operator, count=self.count)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        if not isinstance(data, dict):
            raise ValueError("Each rule must be a JSON object.")
        fields = {"source", "target", "neighbor_type", "operator", "count"}
        if set(data) - fields:
            raise ValueError("Unknown rule fields: " + ", ".join(sorted(set(data) - fields)))
        if not {"source", "target"} <= data.keys():
            raise ValueError("Each rule requires source and target.")
        return cls(**data)


def rules_from_json(text: str, cell_types: Iterable[str]) -> list[Rule]:
    """Decode a JSON array and validate every rule against the allowed types."""
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("Rules must be a JSON array.")
    allowed = validate_cell_types(list(cell_types))
    rules = []
    for item in data:
        rule = Rule.from_dict(item)
        rule.validate_types(allowed)
        rules.append(rule)
    return rules


def rules_to_json(rules: Iterable[Rule]) -> str:
    return json.dumps([rule.to_dict() for rule in rules], indent=2)


def save_rules(rules: Iterable[Rule], directory: str | Path) -> Path:
    """Save a new numbered JSON file without overwriting an earlier rule set."""
    text = rules_to_json(rules)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    number = 1
    while True:
        path = directory / f"rules_{number:03d}.json"
        try:
            with path.open("x", encoding="utf-8") as file:
                file.write(text + "\n")
            return path
        except FileExistsError:
            number += 1


def next_cell_type(current_type: str, neighbor_counts: Mapping[str, int], rules: Iterable[Rule]) -> str:
    """First matching rule wins; with no match, the cell keeps its state."""
    for rule in rules:
        if rule.matches(current_type, neighbor_counts):
            return rule.target
    return current_type
