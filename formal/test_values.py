"""Records, helpers, optional faults, and checked source permissions."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from rmverify import Specification, verify
from rmverify.checking import prepare_model, differential
from rmverify.frontend import Unsupported
from rmverify import typed_backend
from examples.messages_spec import spec, Message
from examples.collections_spec import registry


class ValueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load(self, source):
        path = self.root/'values_fixture.py'
        path.write_text(source)
        entry = importlib.util.spec_from_file_location('values_fixture',path)
        module = importlib.util.module_from_spec(entry)
        sys.modules[entry.name] = module
        exec(compile(source,str(path),'exec'),module.__dict__)
        return module

    def test_records_helpers_and_record_keys(self):
        report = verify(spec,directory=self.root,timeout=90,depth=2)
        self.assertTrue(report.ok,report)
        machine = spec.target()
        machine.put(3,7); machine.put(3,7)
        self.assertEqual(machine.table,{Message(3,7):7})
        self.assertEqual(machine.total,7)
        artifact = json.loads((Path(report.evidence)/'artifact.json').read_text())
        self.assertGreater(len(artifact['programs']),len(spec.transitions)+2)
        self.assertIn("'Verified.ownership0'",(Path(report.evidence)/'Translation.log').read_text())

    def test_frozen_behavior_cannot_be_patched(self):
        with patch.object(Message,'__eq__',lambda a,b: True):
            with self.assertRaisesRegex(Unsupported,'frozen dataclass behavior'):
                prepare_model(spec)

    def test_defaults_keywords_and_optional_dictionary_values(self):
        m = self.load('''from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Box:
    value: int = 0
    flag: bool = False
class State:
    entries: dict[int,Box | None]
    latest: Box | None
    def __init__(self) -> None:
        self.entries = {1: None}
        self.latest = None
    def step(self, value:int) -> None:
        self.entries[1] = Box(flag=False,value=value)
        self.latest = self.entries.get(1)
def safe(s:State) -> bool:
    return s.latest is None or s.latest.value == s.latest.value
''')
        report = verify(Specification(m.State,[m.State.step],invariants=[m.safe]),directory=self.root,timeout=90,depth=1)
        self.assertTrue(report.ok,report)

    def test_optional_field_fault_is_checked(self):
        m = self.load('''from dataclasses import dataclass
@dataclass(frozen=True)
class Message:
    value:int
class State:
    message:Message | None
    value:int
    def __init__(self) -> None:
        self.message = None
        self.value = 0
    def step(self) -> None:
        self.value = self.message.value
def safe(s:State) -> bool:
    return s.value >= 0
''')
        report = verify(Specification(m.State,[m.State.step],invariants=[m.safe]),directory=self.root,timeout=90,depth=1)
        self.assertEqual(report.translation,'proved',report)
        self.assertEqual(report.properties['no-fault']['status'],'refuted',report)
        self.assertEqual(report.properties['no-fault']['witness']['fault'],'missingValue')

    def test_set_predicate_helpers_require_totality(self):
        source = '''def predicate(k:int, entries:dict[int,int]) -> bool:
    return EXPRESSION
class State:
    ids:set[int]
    entries:dict[int,int]
    count:int
    def __init__(self) -> None:
        self.ids = {1,2}
        self.entries = {}
        self.count = 0
    def step(self) -> None:
        if all(predicate(k,self.entries) for k in self.ids):
            self.count += 1
def safe(s:State) -> bool:
    return s.count >= 0
'''
        m = self.load(source.replace('EXPRESSION','entries.get(k,0) >= 0'))
        report = verify(Specification(m.State,[m.State.step],invariants=[m.safe]),directory=self.root,timeout=90,depth=1)
        self.assertTrue(report.ok,report)
        audits = (Path(report.evidence)/'Translation.log').read_text()
        self.assertIn('Verified.set_total',audits)
        self.assertIn('Verified.set_order',audits)
        m = self.load(source.replace('EXPRESSION','entries[k] >= 0'))
        report = verify(Specification(m.State,[m.State.step],invariants=[m.safe]),directory=self.root,timeout=90,depth=1)
        self.assertNotEqual(report.translation,'proved',report)
        self.assertTrue((Path(report.evidence)/'Translation.lean').exists(),report)

    def test_borrow_certificates_detect_invalid_access(self):
        original = typed_backend.borrow_certificate
        def corrupt(p,i):
            if p.loans:
                p.accesses.append(dict(owner=p.loans[0]['owner'],via=None,write=True,position=p.loans[0]['finish']))
            return original(p,i)
        with patch.object(typed_backend,'borrow_certificate',corrupt):
            report = verify(registry,directory=self.root,timeout=90,depth=1)
        self.assertNotEqual(report.translation,'proved',report)
        self.assertTrue((Path(report.evidence)/'Translation.lean').exists(),report)


if __name__=='__main__': unittest.main()
