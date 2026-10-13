import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from network import CycleNetwork, cole_vishkin_palette_schedule, log_star  # noqa: E402
from node import SymmetryBreakingError  # noqa: E402
from validator import Validator as V  # noqa: E402


class TestWithIds(unittest.TestCase):
    def test_always_proper_three_coloring(self):
        for seed in range(300):
            rng = random.Random(seed)
            n = rng.choice([3, 4, 5, 6, 7, 10, 33, 100])
            N = rng.choice([n, n + 1, 2 * n, n ** 2, 10 ** 9, 2 ** 200])
            net = CycleNetwork(n, N, seed=seed)
            net.execute_simulation()  # verify() runs inside
            self.assertTrue(net.is_proper)
            self.assertLessEqual(len(set(net.colors)), 3)

    def test_ids_are_unique(self):
        net = CycleNetwork(50, 60, seed=1)
        ids = [node.id for node in net.cycle]
        self.assertEqual(len(set(ids)), 50)

    def test_smallest_cases(self):
        net = CycleNetwork(3, 3, ids=[2, 0, 1])
        self.assertEqual(net.execute_simulation(), 0)  # already a proper 3-coloring

    def test_rounds_match_schedule(self):
        net = CycleNetwork(200, 200 ** 3, seed=3)
        rounds = net.execute_simulation()
        cv_rounds = len(cole_vishkin_palette_schedule(200 ** 3)) - 1
        self.assertLessEqual(rounds, cv_rounds + 3)

    def test_rounds_do_not_depend_on_which_ids_were_drawn(self):
        r = {CycleNetwork(64, 10 ** 6, seed=s).execute_simulation() for s in range(20)}
        self.assertEqual(len(r), 1)

    def test_message_accounting(self):
        net = CycleNetwork(10, 10 ** 3, seed=0)
        net.execute_simulation()
        cv = len(cole_vishkin_palette_schedule(10 ** 3)) - 1
        greedy = net.rounds_executed - cv
        self.assertEqual(net.message_complexity, 10 * cv + 20 * greedy)

    def test_log_star_values(self):
        self.assertEqual([log_star(x) for x in (1, 2, 4, 16, 65536, 2 ** 65536)], [0, 1, 2, 3, 4, 5])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            CycleNetwork(2)
        with self.assertRaises(ValueError):
            CycleNetwork(10, id_space=5)
        with self.assertRaises(ValueError):
            CycleNetwork(3, 10, ids=[1, 1, 2])


class TestAnonymous(unittest.TestCase):
    def test_all_nodes_identical_initially(self):
        net = CycleNetwork(20, anonymous=True)
        self.assertTrue(net.all_states_identical())
        self.assertEqual(net.count_distinct_views(5), 1)

    def test_cole_vishkin_cannot_start(self):
        net = CycleNetwork(20, anonymous=True)
        with self.assertRaises(SymmetryBreakingError):
            net.execute_simulation()

    def test_any_deterministic_rule_preserves_symmetry(self):
        for seed in range(50):
            rng = random.Random(seed)
            table = {}

            def rule(own, succ, pred):
                key = (own, succ, pred)
                if key not in table:
                    table[key] = rng.randrange(8)
                return table[key]

            net = CycleNetwork(12, anonymous=True)
            for _ in range(6):
                net.run_generic_rounds(rule, 1)
                self.assertTrue(net.all_states_identical())
            self.assertFalse(V.is_proper_coloring([s % 3 for s in net.colors]))


if __name__ == "__main__":
    unittest.main()
