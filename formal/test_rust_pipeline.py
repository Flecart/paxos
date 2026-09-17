"""Input and proof-boundary regression tests; optional end-to-end extraction.

python3 -m unittest formal.test_rust_pipeline -v
RMVERIFY_RUST_INTEGRATION=1 python3 -m unittest formal.test_rust_pipeline -v
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
from formal import rust_verify as engine


class RustPipelineTests(unittest.TestCase):
    def test_zip_rejects_escape_and_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('../escape', '/absolute', 'a\\b'):
                archive = root / 'code.zip'
                with zipfile.ZipFile(archive, 'w') as z:
                    z.writestr(name, 'bad')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    engine.unpack(archive, root / name.replace('/', '_').replace('\\', '_'))
            with zipfile.ZipFile(root / 'link.zip', 'w') as z:
                item = zipfile.ZipInfo('link')
                item.external_attr = 0o120777 << 16
                z.writestr(item, '/etc/passwd')
            with self.assertRaises(ValueError):
                engine.unpack(root / 'link.zip', root / 'unpacked-link')

    def test_nested_zip_and_single_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(root / 'code.zip', 'w') as z:
                z.writestr('project/Cargo.toml', '[package]\nname="x"\nversion="0.1.0"')
                z.writestr('project/src/lib.rs', 'pub fn identity(x: u64) -> u64 { x }')
            crate = engine.unpack(root / 'code.zip', root / 'zip')
            self.assertEqual(crate, root / 'zip/project')
            single = engine.unpack(crate / 'src/lib.rs', root / 'single')
            self.assertTrue((single / 'Cargo.toml').exists())

    def test_axiom_audit_rejects_sorry_custom_axioms_and_missing_output(self):
        engine.audit("'Check.test' depends on axioms: [propext, Classical.choice, Quot.sound]", ['Check.test'])
        for text in ("'Check.test' depends on axioms: [sorryAx]",
                     "'Check.test' depends on axioms: [assumeSafety]", ''):
            with self.subTest(text=text), self.assertRaises(ValueError):
                engine.audit(text, ['Check.test'])

    def test_snapshot_does_not_recurse_into_its_own_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'Cargo.toml').write_text('[package]\nname="x"\nversion="0.1.0"')
            destination = root / 'output/run/source'
            engine.unpack(root, destination)
            self.assertTrue((destination / 'Cargo.toml').exists())
            self.assertFalse((destination / 'output').exists())

    def test_binary_only_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'crate'
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text('[package]\nname="x"\nversion="0.1.0"')
            (source / 'src/main.rs').write_text('fn main() {}')
            request = root / 'request.json'
            request.write_text('{"claims":[{"name":"test","statement":"True"}]}')
            report = engine.verify(source, request, root / 'evidence')
            self.assertEqual(report['status'], 'unsupported')

    def test_requests_require_formal_statements(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'request.json'
            for request in ({'claims': ['prove my program correct']}, {'claims': []},
                            {'profile': 'paxos', 'claims': ['anything']}):
                path.write_text(json.dumps(request))
                with self.assertRaises(ValueError):
                    engine.load_request(path)

    @unittest.skipUnless(os.environ.get('RMVERIFY_RUST_INTEGRATION') == '1', 'requires pinned extraction tools')
    def test_custom_source_checked_proof_refutation_and_sorry_rejection(self):
        with tempfile.TemporaryDirectory(dir=engine.ROOT / '.rmverify') as tmp:
            root = Path(tmp)
            source = root / 'identity.rs'
            source.write_text('pub fn identity(x: u64) -> u64 { x }')
            request = root / 'statements.json'
            request.write_text(json.dumps({'claims': [
                {'name': 'identity',
                 'statement': '∀ x : Aeneas.Std.U64, user_protocol.identity x = Aeneas.Std.RustM.ok x',
                 'proof': 'by intro x; rfl'},
                {'name': 'false_claim', 'statement': 'False', 'proof': 'by simp'},
                {'name': 'no_sorry', 'statement': 'True', 'proof': 'by sorry'},
            ]}))
            result = engine.verify(source, request, root / 'evidence', timeout=600)
            self.assertEqual(result['properties']['identity']['status'], 'proved', result)
            self.assertEqual(result['properties']['false_claim']['status'], 'refuted', result)
            self.assertEqual(result['properties']['no_sorry']['status'], 'unknown', result)

    @unittest.skipUnless(os.environ.get('RMVERIFY_RUST_INTEGRATION') == '1', 'requires pinned extraction tools')
    def test_paxos_directory_zip_replay_and_mutation(self):
        with tempfile.TemporaryDirectory(dir=engine.ROOT / '.rmverify') as tmp:
            root = Path(tmp)
            source = engine.ROOT / 'formal/rust/paxos'
            request = engine.ROOT / 'formal/rust/requests-paxos.json'
            result = engine.verify(source, request, root / 'evidence', timeout=600)
            self.assertEqual(result['status'], 'proved', result)
            self.assertEqual(engine.recheck(result['evidence'])['rechecked'], 2)
            archive = root / 'paxos.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for relative in ('Cargo.toml', 'src/lib.rs'):
                    z.write(source / relative, 'paxos/' + relative)
                z.writestr('paxos/src/main.rs', 'fn main() { println!(\"runtime excluded\"); }')
            zipped = engine.verify(archive, request, root / 'evidence', timeout=600)
            self.assertEqual(zipped['status'], 'proved', zipped)
            mutant = engine.unpack(archive, root / 'mutant')
            path = mutant / 'src/lib.rs'
            path.write_text(path.read_text().replace('if b.ballot > a.ballot', 'if b.ballot < a.ballot'))
            broken = engine.verify(mutant, request, root / 'evidence', timeout=600)
            self.assertNotEqual(broken['status'], 'proved', broken)
            self.assertIn('select_eq', (Path(broken['evidence']) / 'build.log').read_text())
            path.write_text((source / 'src/lib.rs').read_text().replace('if first >= 3', 'if first >= 0'))
            stalled = engine.verify(mutant, request, root / 'evidence', timeout=600)
            self.assertEqual(stalled['status'], 'unknown', stalled)
            self.assertRegex((Path(stalled['evidence']) / 'build.log').read_text(),
                             r"'PaxosBridge\.liveness' depends on axioms: \[[^\]]*sorryAx")


if __name__ == '__main__':
    unittest.main()
