"""Regression checks for the separate model; Python checks are not proofs."""
from copy import deepcopy
from itertools import combinations, permutations
from pathlib import Path
import unittest
from unittest.mock import patch

from rmverify import verify
from rmverify.checking import check_trace, differential, prepare_model
from examples.paxos_model import AcceptorState, BallotValue, PaxosAcceptorModel, PaxosSafetyModel, Vote, promise
from examples.paxos_model_spec import acceptor, acceptors_valid, agreement, adoption_trace, spec


def prepare_quorum(model, ballot, offered, quorum):
    model.phase1a(ballot)
    for member in quorum:
        model.phase1b(member, ballot)
    model.phase2a(ballot, offered, *quorum)


class PaxosModelTests(unittest.TestCase):
    def test_local_promises_and_duplicate_accept(self):
        model = PaxosAcceptorModel()
        model.receive_accept(0, 7)
        model.prepare(2)
        promised = model.state
        model.receive_accept(1, 9)
        model.prepare(-1)
        self.assertEqual(model.state, promised)
        model.receive_accept(2, 7)
        model.receive_accept(2, 7)
        self.assertEqual(model.state, AcceptorState(2, BallotValue(2, 7)))
        # The protocol, not this local acceptor, enforces one proposal per ballot.
        model.receive_accept(2, 9)
        self.assertEqual(model.state, AcceptorState(2, BallotValue(2, 9)))

    def test_all_quorum_intersections_preserve_chosen_value(self):
        quorums = list(combinations(range(3), 2))
        for old in quorums:
            for new in quorums:
                for deliveries in permutations(old):
                    with self.subTest(old=old, new=new, deliveries=deliveries):
                        model = PaxosSafetyModel()
                        prepare_quorum(model, 0, 7, old)
                        for member in deliveries:
                            model.phase2b(member, 0)
                            model.phase2b(member, 0)
                        model.learn(0, 7, *old)
                        self.assertEqual(model.chosen, {7})
                        prepare_quorum(model, 1, 9, new)
                        self.assertEqual(model.proposals[1], 7)
                        for member in new:
                            model.phase2b(member, 1)
                            model.phase2b(member, 0)  # delayed old request
                        model.learn(1, 7, *new)
                        model.learn(0, 7, *old)  # retained historical votes
                        self.assertEqual(model.chosen, {7})
                        self.assertTrue(agreement(model))

    def test_highest_ballot_wins_even_before_any_value_is_chosen(self):
        model = PaxosSafetyModel()
        prepare_quorum(model, 0, 7, (0, 1))
        model.phase2b(0, 0)
        prepare_quorum(model, 1, 9, (1, 2))
        model.phase2b(1, 1)
        model.phase2b(1, 0)  # the old, unfinished ballot cannot gain this vote
        model.learn(0, 7, 0, 1)
        self.assertEqual(model.chosen, set())
        prepare_quorum(model, 2, 11, (0, 1))
        self.assertEqual(model.proposals[2], 9)
        model.phase2b(0, 2)
        model.phase2b(1, 2)
        model.learn(2, 9, 0, 1)
        self.assertEqual(model.chosen, {9})

    def test_no_fabrication_duplicate_quorum_or_ballot_reuse(self):
        model = PaxosSafetyModel()
        initial = deepcopy(vars(model))
        model.phase1a(-1)
        model.phase1b(0, 0)  # no prepare message
        model.phase1b(99, 0)
        model.phase2a(0, 7, 0, 1)  # no promise quorum
        model.phase2b(0, 0)  # no proposal
        model.learn(0, 7, 0, 1)  # no votes
        self.assertEqual(vars(model), initial)
        model.phase1a(0)
        model.phase1b(0, 0)
        model.phase1b(0, 0)
        model.phase2a(0, 7, 0, 0)
        self.assertEqual(model.proposals, {})
        model.phase1b(1, 0)
        model.phase2a(0, 7, 0, 1)
        model.phase2a(0, 9, 0, 1)
        self.assertEqual(model.proposals, {0: 7})
        model.phase2b(0, 0)
        model.phase2b(0, 0)
        self.assertEqual(model.votes, {Vote(0, 0, 7)})
        model.learn(0, 7, 0, 0)
        self.assertEqual(model.chosen, set())

    def test_source_differential_and_multiballot_trace(self):
        for specification in (acceptor, spec):
            differential(prepare_model(specification))
        self.assertEqual(check_trace(prepare_model(spec), adoption_trace)['status'], 'passed')

    def test_current_strengthening_has_an_induction_gap(self):
        # This fabricated state is an induction counterexample, not a reachable
        # protocol execution. It explains why local acceptor facts do not suffice.
        candidate = PaxosSafetyModel()
        candidate.chosen = {7}
        candidate.votes = {Vote(0, 1, 9), Vote(1, 1, 9)}
        self.assertTrue(agreement(candidate) and acceptors_valid(candidate))
        candidate.learn(1, 9, 0, 1)
        self.assertFalse(agreement(candidate))

    def test_lean_acceptor(self):
        report = verify(acceptor, timeout=120, depth=2)
        self.assertTrue(report.ok, report)

    def test_safe_helper_corruption_fails_correspondence(self):
        from rmverify import typed_backend
        original = typed_backend.compiled_definition

        def corrupt(program, index):
            lines, names = original(program, index)
            if program.function is promise:
                changed = [line.replace('«promised» := a.1', '«promised» := a.1 + 1') for line in lines]
                self.assertNotEqual(changed, lines)
                lines = changed
            return lines, names

        with patch.object(typed_backend, 'compiled_definition', corrupt):
            report = verify(acceptor, timeout=120, depth=0)
        self.assertNotEqual(report.translation, 'proved', report)
        self.assertTrue((Path(report.evidence) / 'Translation.lean').exists(), report)

    def test_lean_protocol_correspondence(self):
        report = verify(spec, timeout=180, depth=2)
        self.assertEqual(report.translation, 'proved', report)
        self.assertIn(report.status, ('proved', 'unknown'), report)
        self.assertTrue(all(c['status'] == 'passed' for c in report.checks), report)
        self.assertIn('source_model_eq', (Path(report.evidence) / 'Translation.log').read_text())


if __name__ == '__main__':
    unittest.main()
