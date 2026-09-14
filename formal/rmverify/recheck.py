"""Standalone evidence replay: copy this file with the evidence; no rmverify import."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def audit(text, names):
    for name in names:
        if f"'{name}' does not depend on any axioms" in text:
            continue
        match = re.search(rf"'{re.escape(name)}' depends on axioms:\s*\[([^\]]*)\]", text, re.S)
        if match is None or not {n.strip() for n in match[1].split(',') if n.strip()} <= {
            'propext', 'Classical.choice', 'Quot.sound'
        }:
            raise ValueError(f"missing or unapproved axiom audit: {name}")


def lean_environment(directory):
    """Use the pinned Lake package layout without reloading package configuration."""
    manifest = json.loads((directory/'lake-manifest.json').read_text())
    libraries = [directory/'.lake/build/lib/lean']
    libraries += [directory/'.lake/packages'/p['name']/'.lake/build/lib/lean' for p in manifest['packages']]
    return dict(os.environ, LEAN_PATH=os.pathsep.join(str(p) for p in libraries),
                ELAN_TOOLCHAIN=(directory/"lean-toolchain").read_text().strip())


def solver_plugins(directory, source):
    if not any(tactic in source for tactic in ('veil_smt','veil_bmc')):return []
    library=directory/'.lake/packages/cvc5/.lake/build/lib/libcvc5_cvc5.so'
    if sys.platform=='darwin':library=library.with_suffix('.dylib')
    if not library.exists():raise ValueError('build the pinned CVC5 shared library before running SMT reconstruction')
    return ['--plugin='+str(library.resolve())]


def main():
    directory = Path(__file__).resolve().parent
    manifest = json.loads((directory/'recheck.json').read_text())
    for name, digest in manifest['files'].items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"evidence content changed: {name}")
    if not (directory/'.lake/packages/veil/.lake/build/lib/lean/Veil.olean').exists():
        subprocess.run(['lake', '--no-cache', 'build', '+Veil'], cwd=directory, check=True)
    (directory/'.lake/build/lib/lean').mkdir(parents=True, exist_ok=True)
    for obligation in manifest['obligations']:
        name = obligation['name']
        args = ['lean', '-j1', *solver_plugins(directory,(directory/f'{name}.lean').read_text()), f'{name}.lean']
        if obligation['output']:
            args += ['-o', str(directory/'.lake/build/lib/lean'/f'{name}.olean')]
        result = subprocess.run(args, cwd=directory, env=lean_environment(directory), capture_output=True, text=True,
                                timeout=manifest['timeout'])
        (directory/f'{name}.recheck.log').write_text(result.stdout+result.stderr)
        if result.returncode:
            raise ValueError(f"Lean rejected {name}; see {name}.recheck.log")
        audit(result.stdout, obligation['audits'])
    print(f"Rechecked {len(manifest['obligations'])} accepted obligations; see report.json for claim statuses.")


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
