# CelLab: initial model

Run `python main.py` with Python 3.10 or later. No runtime dependencies.
Enter two positive integers, comma-separated string cell types, and a default
cell type. Every cell initially has that default type. Coordinates are zero-based.
The program then asks you to define rules through guided prompts and saves them
as JSON automatically. You do not need to prepare a rules file.
Type names are case-sensitive; surrounding whitespace is removed during input.
Use `world.set_cell(row, column, type_name)` for a custom initial configuration.
`world.snapshot()` returns an independent matrix copy. Each matrix row is independent.

## File division

Implemented:
- `main.py`: guided setup and rule entry, validation/retry prompts, and the generation loop.
- `cell_types.py`: checks that the string type names are nonempty and unique.
- `automaton.py`: dimensions, allowed states, matrix initialization and cell assignment.
- `rules.py`: rule definitions, JSON conversion/saving, type validation and condition evaluation.
- `examples/brians_brain_rules.json`: an example rule set.
- `test_rules.py`: rule evaluation and validation tests (`python -B -m unittest -v`).
- `test_main.py`: guided input, validation retries, saved rules, and the main loop.
- `simulation.py`: neighbor counting and simultaneous one-generation updates.
- `test_simulation.py`: known transitions for three automata and edges.

Suggested next files (not implemented):
- `storage.py`: JSON save/load of the definition, parameters, current generation
  number and matrix; validate loaded data before constructing a world.
- `examples.py`: definitions and starting configurations for 2-3 automata.
- `parser.py`: later natural-language input translated into the same model objects.

## Recommended rule design

Keep state names as strings, but represent rules as data instead of executable
strings. Start with a small rule record, for example:

```python
Rule(source="OFF", target="FIRING", neighbor_type="FIRING", operator="==", count=2)
Rule(source="FIRING", target="DYING")  # unconditional transition
Rule(source="DYING", target="OFF")
```

This interface is implemented in `rules.py`. An absent
neighbor condition means an unconditional transition. Restrict operators to an
explicit set such as `==`, `!=`, `<`, `<=`, `>`, `>=`; compare counts through
ordinary Python conditions or operator functions. Validate source, target and
neighbor types against the automaton's allowed types. Do not use eval or exec.
A rule's description can be a string for display, without being its executable form.

Choose and store neighborhood (eight surrounding cells or four orthogonal cells)
and boundary handling (ignore outside positions or wrap around). Recommended
initial defaults: eight neighbors, ignore outside positions, exclude the center.
Evaluate rules in list order; the first matching rule supplies the next state.
If none matches, retain the current state. Always read all conditions from the
old matrix and write results into a separate new matrix before replacing it.

For Brian's Brain, use the three rules above. For deterministic Forest Fire,
use FIRE -> EMPTY unconditionally and TREE -> FIRE when FIRE-neighbor count >= 1.
For Crystal Growth, use EMPTY -> CRYSTAL when CRYSTAL-neighbor count == 1.
These three examples fit this first rule model. Movement, numerical values,
cell ages, and multi-cell actions will require extensions to the model.

Later flow: natural-language description -> parser -> validated rule objects ->
simulation. Until then, use the console prompts or construct the same objects
directly in Python. JSON stores their fields without changing the rule meaning.

## Deliverable 2 status

The project PDF requires world state and rules, experiment parameters, state
storage/recovery, and applying rules to generate new states on 2-3 automata.
This version implements initialization, JSON rules and simulation, with tests on
Brian's Brain, deterministic Forest Fire, and Crystal Growth. State storage and
recovery and optional history retention remain to be implemented. Saving rule
definitions is supported; saving rules alone does not save the world or generation.
The natural-language parser belongs to deliverable 4 in the supplied schedule.

## Using JSON rules

```python
from pathlib import Path
from rules import rules_from_json, rules_to_json, next_cell_type

text = Path("examples/brians_brain_rules.json").read_text(encoding="utf-8")
rules = rules_from_json(text, ["OFF", "FIRING", "DYING"])
assert next_cell_type("OFF", {"FIRING": 2}, rules) == "FIRING"
json_text = rules_to_json(rules)
```

The JSON root is an array; each object requires `source` and `target`.
Conditional rules also supply `neighbor_type`, `operator`, and `count` together.
Counts are nonnegative integers. Unknown fields and unknown cell types are rejected
when loading rules. Type names are case-sensitive and should match the world exactly.
An empty rule array keeps every cell unchanged. Directly constructed `Rule` objects
can be checked with `rule.validate_types(world.cell_types)` before use.
The rule evaluator accepts neighbor counts, not a matrix. `simulation.step(world,
rules)` computes those counts and advances the full world by one generation.

## Running iterations

Run `python main.py` and enter dimensions, cell types and a default type. The
program asks for each rule's current type, next type, and optional neighbor
condition. Type names must match the types you defined. Invalid answers prompt
you to try the same field again.

For Brian's Brain, use rows `3`, columns `3`, types `OFF,FIRING,DYING`, and default
`OFF`. Enter the first rule like this:

```text
Current cell type (Enter to finish rules): OFF
Change to cell type: FIRING
Count neighbors of which type? (Enter for an unconditional rule): FIRING
Comparison [exactly]: exactly
Number of neighbors: 2
```

Comparisons accept `exactly`, `at least`, `at most`, `more than`, `fewer than`, or
`not exactly`. You can also use `==`, `>=`, `<=`, `>`, `<`, or `!=`, respectively.
Pressing Enter at the comparison prompt selects `exactly`. Counts must be
nonnegative whole numbers. Rules are applied in entry order, with the first
match winning; no match keeps the current type.

For the second rule, enter current type `FIRING`, next type `DYING`, and press
Enter at the neighbor-type prompt. This creates an unconditional transition.
For the third rule, enter `DYING`, `OFF`, and another blank neighbor type.
Press Enter at the next **current cell type** prompt to finish defining rules.
Finishing before entering any rules creates an empty rule set (no changes).

The program automatically creates `saved_rules` next to `main.py` and saves a
new file such as `rules_001.json`, printing its full path. Each run uses an unused
number, preserving earlier files. These files contain the same JSON array format
shown above and can be loaded through `rules_from_json()`.

Then enter a nonnegative iteration count (for example `2`). Add custom initial
cells as `row column type`: for this example, enter `1 0 FIRING` and `1 2 FIRING`,
then a blank line. Invalid cell entries can be corrected without restarting setup.
Generation 0 is the initial state; each subsequent generation is displayed after
a call to `step()` in the main loop. EOF or Ctrl+C during setup cancels cleanly.

The simulation uses eight surrounding neighbors, excludes the cell itself, and
ignores positions outside the matrix (no wrapping). All cells read the old matrix;
the completed next matrix replaces it only after every cell has been evaluated.
No generations are retained automatically. Use `world.snapshot()` to retain one.
