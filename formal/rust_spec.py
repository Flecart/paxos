"""Versioned, protocol-independent specification elaboration. No tool execution."""
import re

IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z_0-9]*(?:\.[A-Za-z_][A-Za-z_0-9]*)*\Z')
KINDS = {'lean', 'invariant', 'always', 'eventually', 'leads_to'}


def fields(value, allowed, where):
    if not isinstance(value, dict):
        raise ValueError(f'{where} must be an object')
    extra = set(value) - set(allowed.split())
    if extra:
        raise ValueError(f'unknown {where} fields: {sorted(extra)}')


def term(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{where} must be nonempty Lean source')
    return value


def identifiers(value, where):
    if not isinstance(value, list) or any(not isinstance(v, str) or not IDENTIFIER.fullmatch(v) for v in value):
        raise ValueError(f'{where} must be a list of Lean module names')
    return value


def compile_request(request):
    """Return explicit Lean claims; the kernel checks types and resulting proofs.

    Legacy custom Lean requests remain accepted. Named profiles are resolved by
    the caller into ordinary specifications, never dispatched inside this compiler.
    """
    fields(request, 'version title description imports support system claims', 'specification')
    if type(request.get('version', 1)) is not int or request.get('version', 1) != 1:
        raise ValueError('unsupported specification version')
    imports = identifiers(request.get('imports', []), 'imports')
    support = identifiers(request.get('support', []), 'support')
    for key in ('title', 'description'):
        if key in request:
            term(request[key], key)
    system = request.get('system')
    if 'system' in request:
        fields(system, 'module assumptions', 'system')
        term(system.get('module'), 'system.module')
        assumptions = system.get('assumptions')
        if not isinstance(assumptions, list):
            raise ValueError('system.assumptions must be an explicit list (possibly empty)')
        for a in assumptions:
            term(a, 'assumption predicate on executions')
    if not isinstance(request.get('claims'), list) or not request['claims']:
        raise ValueError('claims must be a nonempty list')
    claims = []
    for c in request['claims']:
        fields(c, 'name kind description statement predicate from to proof refutation', 'claim')
        name = c.get('name')
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
            raise ValueError('claim name must be a Lean identifier')
        kind = c.get('kind', 'lean')
        if not isinstance(kind, str) or kind not in KINDS:
            raise ValueError(f'claim {name}: unsupported kind {kind!r}; choose {sorted(KINDS)}')
        for key in ('proof', 'refutation', 'description'):
            if key in c:
                term(c[key], key)
        expected = {'statement'} if kind == 'lean' else ({'from', 'to'} if kind == 'leads_to' else {'predicate'})
        if (set(c) & {'statement', 'predicate', 'from', 'to'}) != expected:
            raise ValueError(f'claim {name} ({kind}) needs exactly {sorted(expected)}')
        for key in expected:
            term(c[key], key)
        if kind == 'lean':
            statement = c['statement']
            used = []  # Any premises are written explicitly in this proposition.
        else:
            if system is None:
                raise ValueError(f'claim {name} ({kind}) needs a system with module and assumptions')
            module = system['module']
            used = [] if kind == 'invariant' else system['assumptions']
            if kind == 'invariant':
                statement = f'RMVerify.Spec.Invariant ({module}) ({c["predicate"]})'
            else:
                env = ' ∧ '.join(f'({a}) run' for a in used) or 'True'
                temporal = {'always': 'Always', 'eventually': 'Eventually', 'leads_to': 'LeadsTo'}[kind]
                args = f'({c["from"]}) ({c["to"]})' if kind == 'leads_to' else f'({c["predicate"]})'
                statement = f'RMVerify.Spec.{temporal} ({module}) (fun run => {env}) {args}'
        claims.append({**c, 'kind': kind, 'statement': statement, 'assumptions': used})
    if len({c['name'] for c in claims}) != len(claims):
        raise ValueError('duplicate claim names')
    return {'imports': imports, 'support': support, 'claims': claims}


def explain_request(request):
    """Preview meaning without claiming that Lean has typechecked the input."""
    compiled = compile_request(request)
    lines = [request.get('title', 'Verification specification'),
             'Preview only: predicates and proofs have not been checked by Lean.']
    for claim in compiled['claims']:
        lines.extend(['', f"{claim['name']} [{claim['kind']}]"])
        if claim.get('description'):
            lines.append(claim['description'])
        lines.append('Assumptions: ' + (', '.join(claim['assumptions']) or
            ('premises written in the Lean statement' if claim['kind'] == 'lean' else 'none')))
        if claim['kind'] == 'invariant':
            lines.append('Must hold in every reachable state, without fairness assumptions.')
        lines.append('Lean: ' + claim['statement'])
        lines.append('Proof: ' + claim.get('proof', 'automatic tactic attempt; success is not guaranteed'))
    return '\n'.join(lines)
