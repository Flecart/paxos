"""Acceptance tests: independent programs, compiler corruption, and failure semantics.

Run: formal/.venv/bin/python formal/test_rmverify.py -v
"""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from rmverify import Call, Specification, Trace, verify
from rmverify import checking, lean_backend
from examples.counter_spec import spec as counter
from examples.programs import (transfer,register,renamed,unstrengthened,strengthened,
                               broken,broken_contract)


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rmverify-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def verify(self,spec,**kwargs):
        return verify(spec,directory=self.root,timeout=30,depth=3,**kwargs)

    def assertProved(self,report):
        self.assertTrue(report.ok,report)
        self.assertEqual(report.translation,"proved")
        text = (Path(report.evidence)/"Invariants.log").read_text()
        self.assertIn("'source_invariant'",text)

    def load(self,source):
        path = self.root / "program.py"
        path.write_text(source)
        entry = importlib.util.spec_from_file_location("acceptance_program",path)
        module = importlib.util.module_from_spec(entry)
        import sys
        sys.modules[entry.name] = module
        entry.loader.exec_module(module)
        return module,path

    def test_unrelated_programs(self):
        for spec in (counter,transfer,register,renamed):
            with self.subTest(program=spec.target.__name__): self.assertProved(self.verify(spec))

    def test_strengthening_is_proved_not_assumed(self):
        report = self.verify(unstrengthened)
        self.assertEqual(report.status,"unknown",report)
        self.assertEqual(report.translation,"proved")
        self.assertProved(self.verify(strengthened))

    def test_refutations_and_preconditions(self):
        report = self.verify(broken)
        self.assertEqual(report.status,"refuted",report)
        self.assertEqual(report.properties['contract:Broken.offer']['status'],'proved')
        witness = report.properties['invariant:broken_nonnegative']['witness']
        self.assertLess(witness['calls'][-1]['arguments']['amount'],0)
        self.assertEqual(self.verify(broken_contract).status,"refuted")

    def test_corrupted_generated_definitions(self):
        original = lean_backend.compiled_definition
        for function in (counter.target.__init__, counter.transitions[0], counter.invariants[0]):
            def corrupt(program, i):
                lines, names = original(program, i)
                if program.function is function:
                    # Safe but incorrect outputs must fail source correspondence.
                    lines[-1] = "  [1]" if program.fields == 0 else "  [17, 0]"
                return lines, names
            with self.subTest(function=function), patch.object(lean_backend, 'compiled_definition', corrupt):
                report = self.verify(counter)
                self.assertTrue((Path(report.evidence)/'Translation.lean').exists(), report)
                self.assertNotEqual(report.translation, 'proved', report)
                self.assertFalse(report.ok)
                self.assertTrue(all(p['status'] != 'proved' for p in report.properties.values()))

    def test_corrupted_state_codecs(self):
        original = lean_backend.definitions
        for name in ('encodeState','decodeState'):
            def corrupt(model):
                source,names = original(model)
                lines = source.splitlines()
                for i,line in enumerate(lines):
                    if line.startswith(f'def {name} '):
                        lines[i] = line.split(' := ')[0] + ' := ' + ('[17]' if name == 'encodeState' else '⟨17⟩')
                return '\n'.join(lines)+'\n',names
            with self.subTest(codec=name), patch.object(lean_backend,'definitions',corrupt):
                report = self.verify(counter)
                self.assertTrue((Path(report.evidence)/'Translation.lean').exists(),report)
                self.assertNotEqual(report.translation,'proved',report)

    def test_invalid_codegen_names_are_rejected(self):
        function = counter.transitions[0]
        original = function.__qualname__
        try:
            function.__qualname__ = "invalid»"
            self.assertEqual(self.verify(counter).status, 'unsupported')
        finally:
            function.__qualname__ = original
        annotations = counter.target.__annotations__
        try:
            counter.target.__annotations__ = {"invalid»": int}
            self.assertEqual(self.verify(counter).status, 'unsupported')
        finally:
            counter.target.__annotations__ = annotations

    def test_unsupported_syntax_and_input_types(self):
        self.assertEqual(Call("offer",method=4).arguments,{"method":4})
        template = '''class Example:
    value: int
    def __init__(self) -> None:
        self.value = 0
    def call(self, x: int) -> None:
        BODY

def safe(s: Example) -> bool:
    return s.value >= 0
'''
        for body in ('print(x)', 'self.value = x * x', 'self.other = x', 'self.value = self.value // 2', 'self.value = missing', 'self.value = True'):
            module,_ = self.load(template.replace('BODY',body))
            report = self.verify(Specification(module.Example,[module.Example.call],invariants=[module.safe]))
            self.assertEqual(report.status,'unsupported',report)
        report = self.verify(replace(counter,checks=[Trace([Call('step',offered=True)])]))
        self.assertFalse(report.ok)
        self.assertEqual(report.checks[0]['status'],'failed')

    def test_large_literals_and_linear_arithmetic(self):
        module,_ = self.load('''class Huge:
    value: int
    def __init__(self) -> None:
        self.value = 18446744073709551616
    def change(self, offered: int) -> int:
        old = self.value
        self.value = max(self.value, 3 * offered - -7)
        return self.value - old

def safe(s: Huge) -> bool:
    return s.value >= 18446744073709551616
''')
        self.assertProved(self.verify(Specification(module.Huge,[module.Huge.change],invariants=[module.safe])))

    def test_source_reload_and_stale_evidence(self):
        module,path = self.load('''class Fresh:
    value: int
    def __init__(self) -> None:
        self.value = 0
    def offer(self, x: int) -> None:
        self.value = max(self.value,x)

def safe(s: Fresh) -> bool:
    return s.value >= 0
''')
        spec = Specification(module.Fresh,[module.Fresh.offer],invariants=[module.safe])
        original = lean_backend.run
        changed = False
        def change_source(*args,**kwargs):
            nonlocal changed
            result = original(*args,**kwargs)
            if not changed:
                path.write_text(path.read_text().replace('max(self.value,x)','min(self.value,x)'))
                changed = True
            return result
        with patch.object(lean_backend,'run',change_source):
            report = self.verify(spec)
        self.assertEqual(report.status,'error',report)
        self.assertTrue(any('stale' in d for d in report.diagnostics))
        self.assertTrue(all(p['status']!='proved' for p in report.properties.values()))
        self.assertEqual(self.verify(spec).status,'unsupported')  # loaded code is stale

    def test_timeout_and_axiom_audit(self):
        timed = verify(counter,directory=self.root,timeout=0.001,depth=1)
        self.assertEqual(timed.status,'unknown',timed)
        (self.root/'lake-manifest.json').write_text(json.dumps({'packages': []}))
        (self.root/'lean-toolchain').write_text((lean_backend.SEMANTICS.parent/'lean-toolchain').read_text())
        with patch.object(subprocess,'Popen') as popen:
            process = popen.return_value
            process.returncode = 0
            process.wait.return_value = 0
            for log in ("", "'claim' depends on axioms: [sorryAx]\n"):
                def fake(*args,**kwargs):
                    kwargs['stdout'].write(log)
                    return process
                popen.side_effect = fake
                status,_ = lean_backend.run(self.root,'Fake','', ['claim'],1)
                self.assertEqual(status,'error')

    def test_cli_and_self_contained_artifacts(self):
        import sys
        result = subprocess.run([sys.executable,'-m','rmverify','examples.counter_spec:spec',
                                 '--out',str(self.root),'--timeout','30'],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report = json.loads(result.stdout)
        artifact = json.loads((Path(report['evidence'])/'artifact.json').read_text())
        self.assertTrue(artifact['sources'])
        self.assertEqual(artifact['version'], 4)
        self.assertNotIn('graphs', artifact)
        self.assertTrue(artifact['dependency_versions']['lean'])
        self.assertIn('source_model_eq',(Path(report['evidence'])/'Translation.lean').read_text())
        replay = subprocess.run([sys.executable, str(Path(report['evidence'])/'recheck.py')],
                                capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stdout+replay.stderr)
        source_path = Path(report['evidence'])/'Translation.lean'
        source_path.write_text(source_path.read_text()+'\n-- changed\n')
        replay = subprocess.run([sys.executable, str(Path(report['evidence'])/'recheck.py')],
                                capture_output=True, text=True)
        self.assertNotEqual(replay.returncode, 0)
        self.assertIn('evidence content changed', replay.stderr)


if __name__ == '__main__':
    unittest.main()
