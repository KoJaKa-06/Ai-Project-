"""Temporary console input, independent of the future natural-language parser."""

from pathlib import Path

from automaton import Automaton
from cell_types import validate_cell_types
from rules import Rule, save_rules
from simulation import step


RULES_DIRECTORY = Path(__file__).resolve().parent / "saved_rules"
COMPARISON_NAMES = {
    "==": "exactly",
    ">=": "at least",
    "<=": "at most",
    ">": "more than",
    "<": "fewer than",
    "!=": "not exactly",
}


def read_integer(prompt: str, minimum: int) -> int:
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Enter a whole number.")
            continue
        if value < minimum:
            print(f"Enter a number greater than or equal to {minimum}.")
            continue
        return value


def read_cell_type(prompt: str, cell_types: tuple[str, ...], allow_blank: bool = False) -> str:
    while True:
        value = input(prompt).strip()
        if (allow_blank and not value) or value in cell_types:
            return value
        print("Choose one of: " + ", ".join(cell_types))


def read_rules(cell_types: tuple[str, ...]) -> list[Rule]:
    """Build validated rules through prompts, preserving their entry order."""
    print("\nDefine the rules. Available cell types: " + ", ".join(cell_types))
    print("The first matching rule wins. With no match, a cell keeps its type.")
    rules = []
    while True:
        print(f"\nRule {len(rules) + 1}")
        source = read_cell_type("Current cell type (Enter to finish rules): ", cell_types, True)
        if not source:
            if not rules:
                print("No rules entered; cells will keep their current types.")
            return rules
        target = read_cell_type("Change to cell type: ", cell_types)
        neighbor_type = read_cell_type(
            "Count neighbors of which type? (Enter for an unconditional rule): ", cell_types, True
        )
        if neighbor_type:
            print("Comparison: " + ", ".join(COMPARISON_NAMES.values()))
            print("You can also enter ==, >=, <=, >, <, or !=.")
            while True:
                choice = input("Comparison [exactly]: ").strip().lower() or "exactly"
                operator = next((symbol for symbol, label in COMPARISON_NAMES.items()
                                 if choice in (symbol, label)), None)
                if operator is not None:
                    break
                print("Choose a comparison from the list above.")
            count = read_integer("Number of neighbors: ", minimum=0)
            rule = Rule(source, target, neighbor_type, operator, count)
            description = f"when {COMPARISON_NAMES[operator]} {count} neighbors are {neighbor_type}"
        else:
            rule = Rule(source, target)
            description = "unconditionally"
        rule.validate_types(cell_types)
        rules.append(rule)
        print(f"Added: {source} -> {target} {description}.")


def main() -> int:
    try:
        rows = read_integer("Rows: ", minimum=1)
        columns = read_integer("Columns: ", minimum=1)
        while True:
            try:
                cell_types = validate_cell_types(input("Cell types, separated by commas: ").split(","))
                break
            except ValueError as error:
                print(error)
        default_type = read_cell_type("Initial/default cell type: ", cell_types)
        world = Automaton(rows, columns, list(cell_types), default_type)
        rules = read_rules(world.cell_types)
        rule_path = save_rules(rules, RULES_DIRECTORY)
        print(f"Rules saved to: {rule_path}")
        iterations = read_integer("Number of iterations: ", minimum=0)
        print("Set initial cells using: row column type (zero-based). Blank line finishes.")
        while True:
            entry = input("Cell: ").strip()
            if not entry:
                break
            try:
                parts = entry.split(maxsplit=2)
                if len(parts) != 3:
                    raise ValueError("Use: row column type, for example 0 0 " + default_type)
                row, column, cell_type = parts
                world.set_cell(int(row), int(column), cell_type)
            except (ValueError, IndexError) as error:
                print(f"Invalid cell: {error}. Try again.")
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.")
        return 1
    except OSError as error:
        print(f"Unable to save rules: {error}")
        return 1

    print("Generation 0:")
    for row in world.matrix:
        print(" ".join(row))
    for generation in range(1, iterations + 1):
        step(world, rules)
        print(f"Generation {generation}:")
        for row in world.matrix:
            print(" ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
