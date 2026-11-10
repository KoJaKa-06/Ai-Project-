import unittest
from automaton import Automaton
from rules import Rule
from simulation import count_neighbors, step


class SimulationTests(unittest.TestCase):
    def test_neighbor_counts(self):
        grid = [['A'] * 3 for _ in range(3)]
        self.assertEqual(count_neighbors(grid, 0, 0), {'A': 3})
        self.assertEqual(count_neighbors(grid, 0, 1), {'A': 5})
        self.assertEqual(count_neighbors(grid, 1, 1), {'A': 8})
        self.assertEqual(count_neighbors([['A']], 0, 0), {})

    def test_forest_fire_updates_simultaneously(self):
        world = Automaton(1, 4, ['TREE', 'FIRE', 'EMPTY'], 'TREE')
        world.set_cell(0, 0, 'FIRE')
        rules = [Rule('FIRE', 'EMPTY'), Rule('TREE', 'FIRE', 'FIRE', '>=', 1)]
        old = world.snapshot()
        for expected in [
            [['EMPTY', 'FIRE', 'TREE', 'TREE']],
            [['EMPTY', 'EMPTY', 'FIRE', 'TREE']],
            [['EMPTY', 'EMPTY', 'EMPTY', 'FIRE']],
            [['EMPTY', 'EMPTY', 'EMPTY', 'EMPTY']],
        ]:
            step(world, rules)
            self.assertEqual(world.matrix, expected)
        self.assertEqual(old, [['FIRE', 'TREE', 'TREE', 'TREE']])

    def test_brians_brain(self):
        world = Automaton(3, 3, ['OFF', 'FIRING', 'DYING'], 'OFF')
        world.set_cell(1, 0, 'FIRING')
        world.set_cell(1, 2, 'FIRING')
        rules = [Rule('OFF', 'FIRING', 'FIRING', '==', 2),
                 Rule('FIRING', 'DYING'), Rule('DYING', 'OFF')]
        step(world, rules)
        self.assertEqual(world.matrix, [['OFF', 'FIRING', 'OFF'],
                                       ['DYING', 'FIRING', 'DYING'],
                                       ['OFF', 'FIRING', 'OFF']])
        step(world, rules)
        self.assertEqual(world.matrix, [['FIRING', 'DYING', 'FIRING'],
                                       ['OFF', 'DYING', 'OFF'],
                                       ['FIRING', 'DYING', 'FIRING']])

    def test_crystal_growth(self):
        world = Automaton(3, 3, ['EMPTY', 'CRYSTAL'], 'EMPTY')
        world.set_cell(1, 1, 'CRYSTAL')
        rules = [Rule('EMPTY', 'CRYSTAL', 'CRYSTAL', '==', 1)]
        step(world, rules)
        self.assertEqual(world.matrix, [['CRYSTAL'] * 3 for _ in range(3)])
        step(world, rules)
        self.assertEqual(world.matrix, [['CRYSTAL'] * 3 for _ in range(3)])

    def test_empty_rules_and_invalid_rule(self):
        world = Automaton(2, 3, ['A'], 'A')
        before = world.snapshot()
        step(world, [])
        self.assertEqual(world.matrix, before)
        with self.assertRaises(ValueError):
            step(world, [Rule('A', 'UNKNOWN')])
        self.assertEqual(world.matrix, before)

if __name__ == '__main__':
    unittest.main()
