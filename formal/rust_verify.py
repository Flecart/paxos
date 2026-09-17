#!/usr/bin/env python3
"""Verify a Rust crate, .rs file, or ZIP against explicit Lean statements.

Local developer tool: Cargo/build scripts and supplied Lean proofs execute code.
Do not expose this command as a service for untrusted uploads without isolation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / '.rmverify/rust-tools'
HAX = TOOLS / 'cargo-hax'
HAX_VERSION = 'cargo-hax-v0.4.0'
HAX_SHA = '5bd1eaf0142ccdf3733e02c2bfdbd24721cfe81d155c045ba0b40a8564f755dd'
RUST = 'nightly-2026-08-18'
LEAN = 'leanprover/lean4:v4.31.0'
PINS = '''[tools]
aeneas = "nightly-2026.09.03-6852e64"
charon = "nightly-2026.09.02"
[versions]
lean = "leanprover/lean4:v4.31.0"
hax-lean-lib = "v0.3.17"
'''
AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}
IGNORED = {'.git', '.lake', '.rmverify', 'target', '__pycache__', '.venv', 'proofs'}
LIMIT = 32 * 1024 * 1024
IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    return dict(os.environ, XDG_CACHE_HOME=str(TOOLS / 'cache'),
                LEAN_NUM_THREADS='2', ELAN_TOOLCHAIN=LEAN)


def run(command, cwd, log, timeout):
    """Keep diagnostic logs and kill the whole process group on timeout."""
    import signal
    with Path(log).open('w') as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment(),
                                   stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise TimeoutError(f'timed out after {timeout}s; see {log}')
    return code


def install():
    if sys.platform != 'linux' or os.uname().machine != 'x86_64':
        raise ValueError('automatic install currently supports Linux x86_64 only')
    TOOLS.mkdir(parents=True, exist_ok=True)
    if not HAX.exists():
        archive = TOOLS / 'cargo-hax.tar.zst'
        url = f'https://github.com/cryspen/hax/releases/download/{HAX_VERSION}/cargo-hax-x86_64-unknown-linux-gnu.tar.zst'
        urllib.request.urlretrieve(url, archive)
        if digest(archive) != HAX_SHA:
            raise ValueError('Hax release checksum mismatch')
        subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(TOOLS), 'cargo-hax'], check=True)
    commands = [
        ['rustup', 'toolchain', 'install', RUST, '--profile', 'minimal',
         '--component', 'rustc-dev,rust-src,llvm-tools'],
        ['elan', 'toolchain', 'install', LEAN],
        [str(HAX), 'hax', 'tools', 'install', 'charon@nightly-2026.09.02'],
        [str(HAX), 'hax', 'tools', 'install', 'aeneas@nightly-2026.09.03-6852e64'],
    ]
    for command in commands:
        subprocess.run(command, env=environment(), check=True)


def unpack(source, destination):
    """Snapshot inputs; reject traversal, links, ambiguous and oversized archives."""
    source = Path(source).resolve()
    destination.mkdir(parents=True)
    if source.is_dir():
        total = 0
        for current, dirs, files in os.walk(source):
            dirs[:] = [d for d in dirs if d not in IGNORED
                       and not destination.is_relative_to(Path(current) / d)]
            for name in dirs + files:
                if (Path(current) / name).is_symlink():
                    raise ValueError('source symlinks are unsupported')
            for name in files:
                path = Path(current) / name
                total += path.stat().st_size
                if total > LIMIT:
                    raise ValueError('source exceeds 32 MiB limit')
                target = destination / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
    elif source.suffix == '.rs':
        if source.stat().st_size > LIMIT:
            raise ValueError('source exceeds 32 MiB limit')
        (destination / 'src').mkdir()
        shutil.copyfile(source, destination / 'src/lib.rs')
        (destination / 'Cargo.toml').write_text(
            '[package]\nname="user-protocol"\nversion="0.1.0"\nedition="2021"\n')
    elif source.suffix == '.zip':
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            if len(infos) > 10000 or sum(i.file_size for i in infos) > LIMIT:
                raise ValueError('archive exceeds file/size limits')
            seen = set()
            for info in infos:
                path = PurePosixPath(info.filename)
                if (path.is_absolute() or '..' in path.parts or '\\' in info.filename
                        or ':' in info.filename or info.filename in seen
                        or stat.S_ISLNK(info.external_attr >> 16)):
                    raise ValueError(f'unsafe/duplicate archive entry: {info.filename}')
                seen.add(info.filename)
                if any(p in IGNORED for p in path.parts):
                    continue
                target = destination.joinpath(*path.parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info) as reader, target.open('wb') as writer:
                        shutil.copyfileobj(reader, writer)
    else:
        raise ValueError('input must be a Rust crate directory, .rs file, or .zip')
    manifests = list(destination.rglob('Cargo.toml'))
    if (destination / 'Cargo.toml').exists():
        return destination
    if len(manifests) != 1:
        raise ValueError('input must contain an unambiguous root Cargo.toml')
    return manifests[0].parent


def audit(text, names):
    for name in names:
        if f"'{name}' does not depend on any axioms" in text:
            continue
        match = re.search(rf"'{re.escape(name)}' depends on axioms:\s*\[([^\]]*)\]", text, re.S)
        if not match:
            raise ValueError(f'missing Lean axiom audit for {name}')
        axioms = {a.strip() for a in match[1].split(',') if a.strip()}
        if axioms - AXIOMS:
            raise ValueError(f'unapproved axioms for {name}: {sorted(axioms - AXIOMS)}')


def load_request(path):
    request = json.loads(Path(path).read_text())
    if not isinstance(request, dict) or not isinstance(request.get('claims'), list) or not request['claims']:
        raise ValueError('statements must contain a nonempty claims list')
    if request.get('profile') == 'paxos':
        if any(c not in ('safety', 'liveness') for c in request['claims']):
            raise ValueError('Paxos profile supports safety and liveness')
    elif 'profile' in request:
        raise ValueError('unknown verification profile')
    else:
        for claim in request['claims']:
            if not isinstance(claim, dict) or not isinstance(claim.get('statement'), str):
                raise ValueError('each custom claim needs an explicit Lean statement')
            if not isinstance(claim.get('name'), str) or not IDENTIFIER.fullmatch(claim['name']):
                raise ValueError('claim name must be a Lean identifier')
            for key in ('proof', 'refutation'):
                if key in claim and not isinstance(claim[key], str):
                    raise ValueError(f'{key} must be Lean source text')
        if not isinstance(request.get('imports', []), list):
            raise ValueError('imports must be a list of Lean module names')
        for name in request.get('imports', []):
            if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
                raise ValueError('imports must be Lean module names')
    names = [c if isinstance(c, str) else c['name'] for c in request['claims']]
    if len(set(names)) != len(names):
        raise ValueError('duplicate claim names')
    return request


def source_hashes(directory):
    return {str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and not any(x in {'.lake', 'target', 'llbc'} for x in p.relative_to(directory).parts)
            and p.suffix not in ('.log', '.olean', '.ilean', '.trace')}


def verify(source, request_path, out, timeout=300):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix='rust-', dir=out))
    report = {'status': 'error', 'translation': 'not-run', 'properties': {},
              'evidence': str(evidence), 'diagnostics': [], 'toolchain': HAX_VERSION,
              'trust_boundary': ['Rust compiler and Charon/Aeneas extraction',
                  'Lean kernel and audited standard axioms',
                  'runtime conforms to the explicit event/ownership/network interface'],
              'scope': 'protocol library; not sockets, executable transport, or crash recovery'}
    try:
        request = load_request(request_path)
        report['properties'] = {(c if isinstance(c, str) else c['name']): {'status': 'not-run'}
                                for c in request['claims']}
        (evidence / 'statements.json').write_text(json.dumps(request, indent=2) + '\n')
        crate = unpack(source, evidence / 'source')
        cargo = tomllib.loads((crate / 'Cargo.toml').read_text())
        library_path = cargo.get('lib', {}).get('path', 'src/lib.rs')
        if 'package' not in cargo or not (crate / library_path).is_file():
            report['status'] = 'unsupported'
            report['diagnostics'].append('Submit one library crate (or a standalone .rs file), not a virtual workspace or binary-only package.')
            return report
        # Hax 0.4.0 does not forward -C --lib on the Aeneas route. Constrain
        # Charon's Cargo invocation explicitly, avoiding binary overwrites.
        charon = TOOLS / 'cache/hax/tools/charon/nightly-2026.09.02/charon'
        if not charon.is_file():
            raise ValueError('pinned Charon unavailable; run --install first')
        wrapper = evidence / 'charon-library'
        wrapper.write_text('#!/usr/bin/env python3\nimport os, sys\n'
            + 'binary = ' + repr(str(charon)) + '\n'
            + 'args = sys.argv[1:]\n'
            + 'if args and args[0] == "cargo":\n'
            + '    if "--" not in args: args.append("--")\n'
            + '    args.append("--lib")\n'
            + 'os.execv(binary, [binary, *args])\n')
        wrapper.chmod(0o755)
        (evidence / 'charon-driver').symlink_to(charon.with_name('charon-driver'))
        # Inputs are preserved; extraction pins are applied only to the snapshot.
        original = crate / 'hax.toml'
        if original.exists():
            shutil.copyfile(original, evidence / 'input-hax.toml')
        original.write_text(PINS.replace('charon = "nightly-2026.09.02"',
            'charon = { path = ' + json.dumps(str(wrapper)) + ' }'))
        if not HAX.exists():
            raise ValueError('extractor unavailable; run formal/rust_verify.py --install first')
        print(f'Extracting Rust into Lean: {evidence}', file=sys.stderr)
        if run([str(HAX), 'hax', 'into', 'lean'], crate, evidence / 'extraction.log', timeout):
            report.update(status='unsupported', translation='failed')
            report['diagnostics'].append('Rust extraction failed; see extraction.log')
            return report
        project = crate / 'proofs/lean'
        roots = list(project.glob('*.lean'))
        if len(roots) != 1:
            raise ValueError('expected exactly one extracted Lean library')
        lib = roots[0].stem
        # Share pinned dependency sources/builds, never extracted code or claims.
        packages = TOOLS / 'lean-packages'
        packages.mkdir(parents=True, exist_ok=True)
        (project / '.lake').mkdir(exist_ok=True)
        (project / '.lake/packages').symlink_to(packages, target_is_directory=True)
        lock = json.loads((ROOT / 'formal/rust/lean-lake-manifest.json').read_text())
        lock['name'] = lib
        (project / 'lake-manifest.json').write_text(json.dumps(lock, indent=2) + '\n')
        if request.get('profile') == 'paxos':
            if lib != 'VerifiedPaxos':
                raise ValueError('Paxos profile expects the verified-paxos library API')
            for name in ('Semantics', 'Temporal', 'Paxos'):
                shutil.copyfile(ROOT / f'formal/rmverify/lean/{name}.lean', project / f'{name}.lean')
            shutil.copyfile(ROOT / 'formal/rust/PaxosBridge.lean', project / 'PaxosBridge.lean')
            report['descriptions'] = {
                'safety': 'all successful learner certificates agree in every reachable state',
                'liveness': 'enabled local handlers return successfully; a stable fair quorum eventually chooses'}
            report['assumptions'] = {
                'safety': ['three non-Byzantine acceptors; two distinct members per quorum',
                    'authenticated retained messages; globally unique proposer ballots',
                    'serialized owned state; no unmodeled reset or corruption'],
                'liveness': ['positive u64 ballot; stable responsive quorum from some time',
                    'weak fairness of its prepare, propose, and accept actions',
                    'quorum promises never exceed that ballot after stabilization']}
            with (project / 'lakefile.toml').open('a') as config:
                for name in ('Semantics', 'Temporal', 'Paxos', 'PaxosBridge'):
                    config.write(f'\n[[lean_lib]]\nname = \"{name}\"\n')
            imports = ['PaxosBridge']
            claims = [{'name': c, 'statement': f'PaxosBridge.{c.capitalize()}Claim',
                       'proof': f'PaxosBridge.{c}'} for c in request['claims']]
        else:
            imports = [f'{lib}.Extraction', *request.get('imports', [])]
            claims = request['claims']
        handwritten = crate / 'verification'
        if handwritten.is_dir():
            shutil.copytree(handwritten, project / 'UserVerification')
            with (project / 'lakefile.toml').open('a') as config:
                config.write('\n[[lean_lib]]\nname = "UserVerification"\n')
        # Build dependencies first; a failure here is not a refutation of a claim.
        root = roots[0]
        root.write_text('\n'.join('import ' + i for i in imports) + '\n')
        print('Building extracted definitions and proof dependencies', file=sys.stderr)
        if run(['lake', 'build'], project, evidence / 'build.log', timeout):
            report.update(status='unknown', translation='extracted')
            for result in report['properties'].values():
                result['status'] = 'unknown'
            report['diagnostics'].append('Lean compilation/refinement failed; see build.log')
            return report
        report['translation'] = 'extracted'
        audited = []
        for index, claim in enumerate(claims):
            module = f'Request{index}'
            theorem = f'VerifiedRequest.claim{index}'
            proof = claim.get('proof', 'by first | rfl | simp_all | omega | grind')
            content = '\n'.join('import ' + i for i in imports)
            content += f'\nset_option maxHeartbeats 1000000\n'
            content += f'theorem {theorem} : {claim["statement"]} :=\n{proof}\n#print axioms {theorem}\n'
            (project / f'{module}.lean').write_text(content)
            log = evidence / f'{module}.log'
            try:
                code = run(['lake', 'env', 'lean', f'{module}.lean'], project, log, timeout)
                if code:
                    result = {'status': 'unknown', 'log': str(log)}
                else:
                    audit(log.read_text(), [theorem])
                    result = {'status': 'proved', 'theorem': theorem, 'statement': claim['statement'], 'log': str(log)}
                    audited.append({'file': f'{module}.lean', 'theorem': theorem})
            except (TimeoutError, ValueError) as error:
                result = {'status': 'unknown', 'diagnostic': str(error), 'log': str(log)}
            if result['status'] == 'unknown' and request.get('profile') != 'paxos':
                negative = claim.get('refutation', 'by first | simp_all | omega | grind')
                negative_module = f'Refutation{index}'
                negative_theorem = f'VerifiedRequest.refutation{index}'
                text = '\n'.join('import ' + i for i in imports)
                text += f'\ntheorem {negative_theorem} : ¬ ({claim["statement"]}) :=\n{negative}\n#print axioms {negative_theorem}\n'
                (project / f'{negative_module}.lean').write_text(text)
                negative_log = evidence / f'{negative_module}.log'
                try:
                    if run(['lake', 'env', 'lean', f'{negative_module}.lean'], project, negative_log, timeout) == 0:
                        audit(negative_log.read_text(), [negative_theorem])
                        result = {'status': 'refuted', 'theorem': negative_theorem,
                                  'statement': claim['statement'], 'log': str(negative_log)}
                        audited.append({'file': f'{negative_module}.lean', 'theorem': negative_theorem})
                except (TimeoutError, ValueError):
                    pass  # A failed search/proof of the negation supplies no evidence.
            report['properties'][claim['name']] = result
        statuses = {c['status'] for c in report['properties'].values()}
        report['status'] = 'proved' if statuses == {'proved'} else ('refuted' if 'refuted' in statuses else 'unknown')
        report['translation'] = 'refinement-proved' if request.get('profile') == 'paxos' and report['status'] == 'proved' else 'extracted'
        manifest = {'project': str(project.relative_to(evidence)), 'obligations': audited,
                    'files': source_hashes(crate), 'source': str(crate.relative_to(evidence)),
                    'timeout': timeout, 'request_sha256': digest(evidence / 'statements.json'),
                    'extractor_wrapper_sha256': digest(wrapper)}
        manifest['report_sha256'] = hashlib.sha256((json.dumps(report, indent=2) + '\n').encode()).hexdigest()
        (evidence / 'recheck.json').write_text(json.dumps(manifest, indent=2) + '\n')
        shutil.copyfile(Path(__file__), evidence / 'rust_verify.py')
        return report
    except TimeoutError as error:
        report['status'] = 'unknown'
        report['diagnostics'].append(str(error))
        return report
    except (ValueError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        report['diagnostics'].append(str(error))
        return report
    finally:
        (evidence / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


def recheck(evidence):
    evidence = Path(evidence).resolve()
    manifest = json.loads((evidence / 'recheck.json').read_text())
    if digest(evidence / 'charon-library') != manifest['extractor_wrapper_sha256']:
        raise ValueError('changed extractor wrapper')
    if digest(evidence / 'report.json') != manifest['report_sha256']:
        raise ValueError('changed verification report')
    if digest(evidence / 'statements.json') != manifest['request_sha256']:
        raise ValueError('changed verification request')
    source = evidence / manifest['source']
    for name, expected in manifest['files'].items():
        if digest(source / name) != expected:
            raise ValueError(f'changed evidence: {name}')
    project = evidence / manifest['project']
    # A copied artifact may not retain the local dependency-cache link.
    packages = project / '.lake/packages'
    if packages.is_symlink() and not packages.exists():
        packages.unlink()
    if run(['lake', 'build'], project, evidence / 'rebuild.log', manifest['timeout']):
        raise ValueError('evidence build failed; see rebuild.log')
    for item in manifest['obligations']:
        log = evidence / (item['file'] + '.recheck.log')
        if run(['lake', 'env', 'lean', item['file']], project, log, manifest['timeout']):
            raise ValueError(f'Lean rejected {item["file"]}')
        audit(log.read_text(), [item['theorem']])
    report = json.loads((evidence / 'report.json').read_text())
    return {'status': report['status'], 'rechecked': len(manifest['obligations']),
            'note': 'unknown claims remain unknown; extraction/compiler boundary remains trusted'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?')
    parser.add_argument('statements', nargs='?')
    parser.add_argument('--out', default=str(ROOT / '.rmverify/rust'))
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--recheck')
    args = parser.parse_args()
    if args.install:
        install()
        if not args.source:
            return 0
    if args.recheck:
        report = recheck(args.recheck)
    else:
        if not args.source or not args.statements:
            parser.error('supply (Rust crate/.rs/.zip, statements.json)')
        report = verify(args.source, args.statements, args.out, args.timeout)
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'proved' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'error', 'diagnostics': [str(error)]}), file=sys.stderr)
        sys.exit(1)
