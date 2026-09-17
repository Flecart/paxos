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

if __package__:
    from .rust_spec import compile_request, explain_request
else:
    from rust_spec import compile_request, explain_request

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
                LEAN_NUM_THREADS='2', ELAN_TOOLCHAIN=LEAN, RUSTUP_TOOLCHAIN=RUST)


def run(command, cwd, log, timeout):
    """Keep diagnostic logs and kill the whole process group on timeout."""
    import signal
    with Path(log).open('w') as output:
        process = subprocess.Popen(command, cwd=cwd, env=environment(),
                                   stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            if isinstance(error, KeyboardInterrupt):
                raise
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
    path = Path(path)
    try:
        request = tomllib.loads(path.read_text()) if path.suffix == '.toml' else json.loads(path.read_text())
    except (ValueError, OSError) as error:
        raise ValueError(f'{path}: {error}') from error
    if isinstance(request, dict) and 'profile' in request:
        if set(request) != {'profile', 'claims'}:
            raise ValueError('a named profile accepts only profile and claims')
        profile = request['profile']
        if not isinstance(profile, str) or not IDENTIFIER.fullmatch(profile):
            raise ValueError('invalid profile name')
        path = ROOT / 'formal/rust/profiles' / (profile + '.json')
        if not path.is_file():
            raise ValueError('unknown verification profile')
        template = json.loads(path.read_text())
        names = request['claims']
        available = {c['name']: c for c in template['claims']}
        if not isinstance(names, list) or not names or any(not isinstance(n, str) or n not in available for n in names):
            raise ValueError('unknown or empty profile claims')
        request = {**template, 'claims': [available[n] for n in names]}
    compile_request(request)
    return request


def discover_spec(source):
    source = Path(source)
    if not source.is_dir():
        raise ValueError('For a .rs or ZIP input, supply the spec.json or spec.toml path explicitly.')
    candidates = [source / name for name in ('spec.toml', 'spec.json') if (source / name).is_file()]
    if len(candidates) != 1:
        raise ValueError('Expected one spec.toml or spec.json in the crate; supply a spec path explicitly if both exist.')
    return candidates[0]


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
        request_path = request_path or discover_spec(source)
        request = load_request(request_path)
        specification = compile_request(request)
        report['properties'] = {c['name']: {'status': 'not-run', 'statement': c['statement'],
            'kind': c['kind'], 'description': c.get('description', ''),
            'assumptions': c['assumptions']} for c in specification['claims']}
        report['title'] = request.get('title', '')
        report['description'] = request.get('description', '')
        (evidence / 'statements.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
        shutil.copyfile(request_path, evidence / 'input-request.json')
        (evidence / 'elaborated.json').write_text(json.dumps(specification, indent=2, ensure_ascii=False) + '\n')
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
        report['translation'] = 'extracted'
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
        (project / 'lake-manifest.json').write_text(json.dumps(lock, indent=2, ensure_ascii=False) + '\n')
        support = list(dict.fromkeys(['Semantics', 'Temporal', 'Specification', *specification['support']]))
        for name in support:
            origin = ROOT / 'formal/rmverify/lean' / (name + '.lean')
            if not origin.is_file():
                raise ValueError(f'unknown shared support module: {name}')
            shutil.copyfile(origin, project / (name + '.lean'))
            with (project / 'lakefile.toml').open('a') as config:
                config.write(f'\n[[lean_lib]]\nname = "{name}"\n')
        imports = [f'{lib}.Extraction', 'Specification', *specification['imports']]
        claims = specification['claims']
        handwritten = crate / 'verification'
        if handwritten.is_dir():
            shutil.copytree(handwritten, project / 'UserVerification')
            with (project / 'lakefile.toml').open('a') as config:
                config.write('\n[[lean_lib]]\nname = "UserVerification"\n')
        # Build dependencies first; a failure here is not a refutation of a claim.
        root = roots[0]
        root.write_text('\n'.join('import ' + i for i in imports) + '\n')
        print('Building extracted definitions and proof dependencies', file=sys.stderr)
        # Build the Rust definitions before independent handwritten models. This
        # avoids loading several large Lean environments concurrently on laptops.
        for targets, filename in (([f'+{lib}.Extraction'], 'extracted-build.log'), ([], 'build.log')):
            if run(['lake', 'build', *targets], project, evidence / filename, timeout):
                report.update(status='unknown', translation='extracted')
                for result in report['properties'].values():
                    result['status'] = 'unknown'
                report['diagnostics'].append(f'Lean compilation/refinement failed; see {filename}')
                report['diagnostics'].extend(line for line in (evidence / filename).read_text().splitlines()
                                             if line.startswith('error: ') and not line.startswith('error: Lean exited'))
                return report
        report['translation'] = 'extracted'
        audited = []
        # The common case checks all claims in one Lean process. Fall back to
        # individual checks to preserve useful partial results on any failure.
        batch_file = project / 'Requests.lean'
        batch_log = evidence / 'Requests.log'
        batch = '\n'.join('import ' + i for i in imports) + '\nset_option maxHeartbeats 1000000\n'
        names = []
        for index, claim in enumerate(claims):
            theorem = f'VerifiedRequest.claim{index}'
            names.append(theorem)
            proof = claim.get('proof', 'by first | rfl | simp_all | omega | grind')
            batch += f'\ntheorem {theorem} : {claim["statement"]} :=\n{proof}\n#print axioms {theorem}\n'
        batch_file.write_text(batch)
        batch_ok = False
        try:
            if run(['lake', 'env', 'lean', batch_file.name], project, batch_log, timeout) == 0:
                audit(batch_log.read_text(), names)
                batch_ok = True
        except (TimeoutError, ValueError):
            pass
        for index, claim in enumerate(claims):
            module = f'Request{index}'
            theorem = f'VerifiedRequest.claim{index}'
            if batch_ok:
                report['properties'][claim['name']].update(status='proved', theorem=theorem, log=str(batch_log))
                audited.append({'file': batch_file.name, 'theorem': theorem})
                continue
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
            if result['status'] == 'unknown':
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
            report['properties'][claim['name']].update(result)
        statuses = {c['status'] for c in report['properties'].values()}
        report['status'] = 'proved' if statuses == {'proved'} else ('refuted' if 'refuted' in statuses else 'unknown')
        # Refinement is an explicit user claim, never inferred from a profile name.
        report['translation'] = 'extracted'
        manifest = {'project': str(project.relative_to(evidence)), 'obligations': audited,
                    'extracted_module': f'{lib}.Extraction',
                    'files': source_hashes(crate), 'source': str(crate.relative_to(evidence)),
                    'timeout': timeout, 'request_sha256': digest(evidence / 'statements.json'),
                    'input_request_sha256': digest(evidence / 'input-request.json'),
                    'elaborated_sha256': digest(evidence / 'elaborated.json'),
                    'extractor_wrapper_sha256': digest(wrapper)}
        manifest['report_sha256'] = hashlib.sha256((json.dumps(report, indent=2, ensure_ascii=False) + '\n').encode()).hexdigest()
        (evidence / 'recheck.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
        shutil.copyfile(Path(__file__), evidence / 'rust_verify.py')
        shutil.copyfile(Path(__file__).with_name('rust_spec.py'), evidence / 'rust_spec.py')
        return report
    except TimeoutError as error:
        report['status'] = 'unknown'
        for result in report['properties'].values():
            if result['status'] == 'not-run':
                result['status'] = 'unknown'
        report['diagnostics'].append(str(error))
        return report
    except (ValueError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        report['diagnostics'].append(str(error))
        return report
    finally:
        (evidence / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')


def recheck(evidence):
    evidence = Path(evidence).resolve()
    manifest = json.loads((evidence / 'recheck.json').read_text())
    if digest(evidence / 'charon-library') != manifest['extractor_wrapper_sha256']:
        raise ValueError('changed extractor wrapper')
    if digest(evidence / 'report.json') != manifest['report_sha256']:
        raise ValueError('changed verification report')
    if digest(evidence / 'statements.json') != manifest['request_sha256']:
        raise ValueError('changed verification request')
    for name, key in (('input-request.json', 'input_request_sha256'), ('elaborated.json', 'elaborated_sha256')):
        if key in manifest and digest(evidence / name) != manifest[key]:
            raise ValueError(f'changed evidence: {name}')
    source = evidence / manifest['source']
    for name, expected in manifest['files'].items():
        if digest(source / name) != expected:
            raise ValueError(f'changed evidence: {name}')
    project = evidence / manifest['project']
    # A copied artifact may not retain the local dependency-cache link.
    packages = project / '.lake/packages'
    if packages.is_symlink() and not packages.exists():
        packages.unlink()
    if manifest.get('extracted_module') and run(['lake', 'build', '+' + manifest['extracted_module']],
            project, evidence / 'rebuild-extracted.log', manifest['timeout']):
        raise ValueError('extracted evidence build failed; see rebuild-extracted.log')
    if run(['lake', 'build'], project, evidence / 'rebuild.log', manifest['timeout']):
        raise ValueError('evidence build failed; see rebuild.log')
    modules = {}
    for item in manifest['obligations']:
        modules.setdefault(item['file'], []).append(item['theorem'])
    for file, names in modules.items():
        log = evidence / (file + '.recheck.log')
        if run(['lake', 'env', 'lean', file], project, log, manifest['timeout']):
            raise ValueError(f'Lean rejected {file}')
        audit(log.read_text(), names)
    report = json.loads((evidence / 'report.json').read_text())
    return {'status': report['status'], 'rechecked': len(manifest['obligations']),
            'note': 'unknown claims remain unknown; extraction/compiler boundary remains trusted'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', help='Rust library directory, .rs file, or ZIP')
    parser.add_argument('statements', nargs='?', help='JSON/TOML spec; defaults to spec.toml or spec.json in a crate directory')
    parser.add_argument('--out', default=str(ROOT / '.rmverify/rust'))
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--recheck')
    parser.add_argument('--explain-spec', metavar='FILE', help='preview claims and assumptions in plain text without running tools')
    parser.add_argument('--check-spec', metavar='FILE', help='validate and print explicit Lean claims without extracting Rust')
    args = parser.parse_args()
    if args.explain_spec:
        print(explain_request(load_request(args.explain_spec)))
        return 0
    if args.check_spec:
        print(json.dumps(compile_request(load_request(args.check_spec)), indent=2, ensure_ascii=False))
        return 0
    if args.install:
        install()
        if not args.source:
            return 0
    if args.recheck:
        report = recheck(args.recheck)
    else:
        if not args.source:
            parser.error('supply a Rust crate, .rs file, or ZIP and optionally a spec.json/spec.toml')
        report = verify(args.source, args.statements, args.out, args.timeout)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'proved' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'error', 'diagnostics': [str(error)]}), file=sys.stderr)
        sys.exit(1)
