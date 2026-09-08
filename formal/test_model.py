"""Small regression checks for the abstraction boundaries, not Paxos correctness."""
import unittest

from runtime import MANIFEST, Network, encode


class ModelChecks(unittest.TestCase):
    def test_value_encoding_keeps_python_types_distinct(self):
        self.assertEqual([encode(v) for v in (None, "A", "B", 0, 1, 2)], list(range(6)))
        for value in (True, False, "C", [], {}):
            with self.assertRaises(ValueError):
                encode(value)

    def test_initial_rm_matches_python(self):
        python, rm = Network(), Network(rm=True)
        for a, b in zip(python.nodes, rm.nodes):
            self.assertEqual([getattr(a, key) for key in MANIFEST["initial"]],
                             [getattr(b, key) for key in MANIFEST["initial"]])

    def test_number_overflow_is_not_a_source_exception(self):
        for rm in (False, True):
            n = Network(rm=rm)
            for _ in range(MANIFEST["max_number"]):
                n.act(("tick", 0))
            self.assertFalse(n.out_of_scope)
            n.act(("tick", 0))
            self.assertTrue(n.out_of_scope)
            self.assertEqual(n.nodes[0].status, 2)
            self.assertEqual(n.nodes[0].fault, 0)

    def test_value_outside_domain_is_explicit(self):
        for rm in (False, True):
            for value in (-1, 6):
                n = Network(rm=rm)
                n.act(("propose", 0, value))
                self.assertTrue(n.out_of_scope)
                self.assertEqual(n.nodes[0].status, 2)

    def test_hook_reentry_and_early_resumption_are_rejected(self):
        n = Network()
        n.act(("propose", 0, 1))
        for action in (("tick", 0), ("resume", 0)):
            with self.assertRaises(ValueError):
                n.act(action)
        with self.assertRaises(ValueError):
            n.act(("tick", -1))
        with self.assertRaises(ValueError):
            n.act(("deliver", -1))

    def test_queue_overflow_is_explicit(self):
        for rm in (False, True):
            n = Network(rm=rm)
            for _ in range(20):
                n.act(("propose", 0, 1))
                if n.out_of_scope:
                    break
                while n.pending:
                    n.act(("deliver", 0))
                n.act(("resume", 0))
            self.assertTrue(n.out_of_scope)
            self.assertEqual(n.nodes[0].fault, 0)


if __name__ == "__main__":
    unittest.main()
