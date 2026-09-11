"""Verification orchestration: compilation is not success until Lean accepts it."""
from dataclasses import asdict
from copy import deepcopy
from .value_types import mutable, matches, probes, json_value
import hashlib
import inspect
import itertools
import json
import marshal
from pathlib import Path
import subprocess
import tempfile

from .api import Report
from .frontend import Unsupported, annotation, fields_of, method_program, parameters, predicate_program
from .execution import execute, ExecutionFault
from . import lean_backend as lean


def prepare_model(spec):
    fields = fields_of(spec.target)
    if not spec.transitions or len(set(spec.transitions)) != len(spec.transitions):
        raise Unsupported("select one or more distinct transition methods")
    for f in spec.transitions:
        if not inspect.isfunction(f) or f.__name__ == "__init__" or getattr(spec.target, f.__name__, None) is not f:
            raise Unsupported("transitions must be methods of the target class")
    if set(spec.contracts) - set(spec.transitions): raise Unsupported("contract for an unselected transition")
    model = dict(target=spec.target, fields=fields, programs=[], methods=[], invariants=[], contracts=[])

    def add(program):
        model["programs"].append(program)
        return len(model["programs"]) - 1

    add(method_program(spec.target.__init__, fields, initialize=True))
    for f in spec.transitions:
        p = method_program(f, fields)
        model["methods"].append(dict(function=f, name=f.__name__, index=add(p), inputs=p.inputs[len(fields):], result=p.result,
                                     parameters=[a.name for a in parameters(f)[1:]]))
    for auxiliary, functions in ((False, spec.invariants), (True, spec.strengthening)):
        for f in functions:
            identifier = ("auxiliary:" if auxiliary else "invariant:") + f.__qualname__
            if any(p["identifier"] == identifier for p in model["invariants"]): raise Unsupported("duplicate property name")
            model["invariants"].append(dict(function=f, identifier=identifier, auxiliary=auxiliary,
                                             index=add(predicate_program(f,fields,spec.target,["state"]))))
    for f,c in spec.contracts.items():
        j = spec.transitions.index(f)
        m = model["methods"][j]
        if c.ensures is None: raise Unsupported("a method contract requires an ensures predicate")
        pre = None if c.requires is None else add(predicate_program(c.requires,fields,spec.target,["state",*m["inputs"]]))
        post = add(predicate_program(c.ensures,fields,spec.target,["state","state",m["result"],*m["inputs"]]))
        model["contracts"].append(dict(method=j, requires=pre, ensures=post, identifier="contract:"+f.__qualname__))
    if not model["invariants"] and not model["contracts"]:
        raise Unsupported("specify at least one invariant or method contract")
    return model


def snapshot(model, obj):
    result = deepcopy([getattr(obj, field) for field in model["fields"]])
    if any(not matches(value, kind) for value, kind in zip(result,model["fields"].values())):
        raise ValueError("runtime state differs from declared types")
    return result


def make_state(model, values):
    obj = object.__new__(model["target"])
    for name, value in zip(model["fields"], values, strict=True): setattr(obj,name,deepcopy(value))
    return obj


def python_program(model, index, values):
    program = model["programs"][index]
    if index == 0:
        obj = object.__new__(model["target"])
        try: program.function(obj)
        except KeyError as error:
            # Uninitialized slots cannot be read by accepted source. They use
            # the same internal defaults as the typed source frame after failure.
            values = [getattr(obj,n, {} if k.startswith("dict[") else set() if k.startswith("set[") else False if k == "bool" else 0)
                      for n,k in model["fields"].items()]
            raise ExecutionFault(values) from error
        return snapshot(model,obj) + [0]
    method = next((m for m in model["methods"] if m["index"] == index), None)
    if method is not None:
        obj = make_state(model,values[:len(model["fields"])])
        try: result = program.function(obj,*values[len(model["fields"]):])
        except KeyError as error: raise ExecutionFault(snapshot(model,obj)) from error
        expected = {"int":int,"bool":bool,"none":type(None)}[method["result"]]
        if type(result) is not expected: raise ValueError("runtime return type mismatch")
        return snapshot(model,obj) + [0 if result is None else result]
    args, cursor = [], 0
    for p in parameters(program.function):
        kind = annotation(p.annotation,model["target"])
        if kind == "state":
            args.append(make_state(model,values[cursor:cursor+len(model["fields"])]))
            cursor += len(model["fields"])
        elif kind == "none": args.append(None)
        else:
            args.append(values[cursor])
            cursor += 1
    result = program.function(*args)
    if type(result) is not bool: raise ValueError("predicate must return bool")
    return [result]


def differential(model):
    count = 0
    for i,p in enumerate(model["programs"]):
        # Fixed deterministic probes; formal equivalence covers all other inputs.
        cases = [probes(k) for k in p.inputs]
        for values in itertools.islice(itertools.product(*cases),128):
            def outcome(run):
                try: return ("ok", run())
                except ExecutionFault as error: return ("fault", "missingKey", error.fields)
                except KeyError: return ("fault", "missingKey", [])
            actual = outcome(lambda: execute(model["programs"][i],values))
            expected = outcome(lambda: python_program(model,i,values))
            if actual != expected: raise ValueError(f"translation mismatch in {p.name}: {values}: Python={expected}, RM={actual}")
            count += 1
    return count


def check_trace(model, trace):
    obj = model["target"]()
    state = execute(model["programs"][0],[])[:len(model["fields"])]
    def invariants():
        for p in model["invariants"]:
            if not p["function"](obj): raise ValueError(f"trace violates {p['identifier']}")
    if snapshot(model,obj) != state: raise ValueError("initialization mismatch")
    invariants()
    observations = [dict(state=dict(zip(model["fields"],state)))]
    for call in trace.calls:
        j = next((j for j,m in enumerate(model["methods"]) if m["name"] == call.method),None)
        if j is None: raise ValueError(f"unselected method {call.method}")
        m = model["methods"][j]
        if set(call.arguments) != set(m["parameters"]): raise ValueError("trace argument names differ from method signature")
        args = [call.arguments[n] for n in m["parameters"]]
        if any(type(v) is not (bool if k == "bool" else int) for v,k in zip(args,m["inputs"])):
            raise ValueError("trace argument type mismatch")
        before = make_state(model,state)
        result = m["function"](obj,*args)
        if type(result) is not {"int":int,"bool":bool,"none":type(None)}[m["result"]]:
            raise ValueError("runtime return type mismatch")
        outputs = execute(model["programs"][m["index"]],state+args)
        if snapshot(model,obj) != outputs[:-1] or (0 if result is None else result) != outputs[-1]:
            raise ValueError("Python/RM trace mismatch")
        state = outputs[:-1]
        invariants()
        for c in model["contracts"]:
            if c["method"] != j: continue
            pre = c["requires"] is None or model["programs"][c["requires"]].function(before,*args)
            if pre and not model["programs"][c["ensures"]].function(before,obj,result,*args):
                raise ValueError(f"trace violates {c['identifier']}")
        observations.append(dict(method=call.method,arguments=call.arguments,state=dict(zip(model["fields"],state)),result=result))
    return dict(status="passed",observations=observations)


def provenance(programs, targets):
    source_paths = {Path(inspect.getsourcefile(target)) for target in targets}
    source_paths.update(Path(inspect.getsourcefile(p.function)) for p in programs)
    files = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    package = Path(__file__).parent
    paths = [*package.glob("*.py"), *package.glob("lean/*.lean"), *package.glob("lean/*.toml"),
             *package.glob("lean/*.json"), package/"lean/lean-toolchain"]
    tools = {str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    import platform
    from importlib.metadata import version
    return dict(sources=files, tooling=tools,
                dependency_versions={"lean": (package/"lean/lean-toolchain").read_text().strip(),
                                     "python": platform.python_version(), "z3-solver": version("z3-solver")})


def function_id(f):
    return None if f is None else [f.__module__, f.__qualname__, hashlib.sha256(marshal.dumps(f.__code__)).hexdigest()]


def identity(spec, model):
    specification = dict(target=[spec.target.__module__,spec.target.__qualname__],
                         initial=function_id(spec.target.__init__), transitions=[function_id(f) for f in spec.transitions],
                         invariants=[function_id(f) for f in spec.invariants], strengthening=[function_id(f) for f in spec.strengthening],
                         contracts=[[function_id(f),function_id(c.requires),function_id(c.ensures)] for f,c in spec.contracts.items()])
    return dict(specification=specification, **provenance(model["programs"], [spec.target]),
                target=spec.target.__qualname__,transitions=[m["name"] for m in model["methods"]],
                properties=[p["identifier"] for p in model["invariants"]]+[c["identifier"] for c in model["contracts"]],
                checks=[asdict(t) for t in spec.checks])


def verify(spec, *, directory=None, timeout=60, depth=10):
    if timeout <= 0 or depth < 0: raise ValueError("timeout must be positive and depth nonnegative")
    parent = Path(directory or ".rmverify").resolve()
    parent.mkdir(parents=True,exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix="check-",dir=parent))
    report = Report("error",evidence=str(evidence))
    status_path = evidence / "report.json"
    status_path.write_text(json.dumps(asdict(report),indent=2,default=json_value)+"\n")
    try:
        model = prepare_model(spec)
        backend = lean
        if any(mutable(k) for p in model["programs"] for k in p.slots):
            from . import typed_backend as backend
        provenance = identity(spec,model)
        artifact = dict(**provenance,version=3,pipeline="Python → Lean RM definitions → checked theorem",fields=model["fields"],programs=[{k:v for k,v in vars(p).items() if k != "function"} for p in model["programs"]],
                        invariants=[{k:v for k,v in p.items() if k != "function"} for p in model["invariants"]],contracts=model["contracts"])
        artifact["sha256"] = hashlib.sha256(json.dumps(artifact,sort_keys=True,default=json_value).encode()).hexdigest()
        (evidence/"artifact.json").write_text(json.dumps(artifact,indent=2,default=json_value)+"\n")
        for p in [*model["invariants"],*model["contracts"]]: report.properties[p["identifier"]] = dict(status="unknown")
        if backend is not lean: report.properties["no-fault"] = dict(status="unknown")
        lean.prepare(evidence)
        lean.build(evidence,timeout,typed=backend is not lean)
        source, names = backend.definitions(model)
        report.translation, diagnostic = lean.run(evidence,"Translation",source,[f"Verified.translation{i}" for i in range(len(model["programs"]))] + ["Verified.source_model_eq"] + [f"Verified.inv_agreement{i}" for i in range(len(model["invariants"]))] + [name for i in range(len(model["contracts"])) for name in (f"Verified.pre_agreement{i}", f"Verified.post_agreement{i}")] + (backend.extra_audits(model) if backend is not lean else ["Verified.encodeState_correct", "Verified.decodeState_correct"]),timeout,output=True)
        if report.translation != "proved":
            report.status = report.translation
            report.diagnostics.append(diagnostic)
            try: differential(model)
            except ValueError as error:
                report.status = report.translation = "error"
                report.diagnostics.append(str(error))
        else:
            report.diagnostics.append(f"{differential(model)} Python/source differential probes passed (regression evidence only)")
            for trace in spec.checks:
                try: report.checks.append(check_trace(model,trace))
                except (ValueError,TypeError,AssertionError) as error: report.checks.append(dict(status="failed",reason=str(error)))
            inv_status, reason = lean.run(evidence,"Invariants",backend.invariant_proof(model,names),["invariant","always_safe","source_invariant","veil_invariant"] + (["no_fault"] if backend is not lean else []),timeout,output=True)
            for p in model["invariants"]: report.properties[p["identifier"]] = dict(status=inv_status)
            if backend is not lean: report.properties["no-fault"] = dict(status=inv_status)
            if reason: report.diagnostics.append(reason)
            for i,c in enumerate(model["contracts"]):
                status, reason = lean.run(evidence,f"Contract{i}",backend.contract_proof(model,names,i,inv_status=="proved"),["contract","source_contract"],timeout)
                report.properties[c["identifier"]] = dict(status=status)
                if reason: report.diagnostics.append(reason)
            unresolved = {key for key,value in report.properties.items() if value["status"] == "unknown"}
            for key in unresolved:
                report.properties[key]["reason"] = "automatic proof did not close; consider additional strengthening predicates"
            if unresolved and backend is lean:
                from .solver import counterexamples
                for identifier, witness in counterexamples(model,depth,timeout,unresolved).items():
                    name = "Witness" + str(list(report.properties).index(identifier))
                    (evidence/f"{name}.json").write_text(json.dumps(witness,indent=2)+"\n")
                    status, reason = lean.run(evidence,name,lean.witness_proof(model,witness),["refutation","source_refutation"],timeout)
                    if status == "proved": report.properties[identifier] = dict(status="refuted",witness=witness)
                    elif reason: report.diagnostics.append(reason)
            if unresolved and backend is not lean:
                for identifier,witness in backend.counterexamples(model,depth,unresolved).items():
                    name = "FaultWitness" if identifier == "no-fault" else "Witness" + str(list(report.properties).index(identifier))
                    (evidence/f"{name}.json").write_text(json.dumps(witness,indent=2,default=json_value)+"\n")
                    status,reason = lean.run(evidence,name,backend.witness_proof(model,witness,names),["refutation","source_refutation"],timeout)
                    if status == "proved": report.properties[identifier] = dict(status="refuted",witness=witness)
                    elif reason: report.diagnostics.append(reason)
            statuses = {p["status"] for p in report.properties.values()}
            report.status = "error" if "error" in statuses else "refuted" if "refuted" in statuses else "unknown" if "unknown" in statuses else "proved"
            if any(c["status"] != "passed" for c in report.checks): report.status = "error"
        if identity(spec,model) != provenance:
            report.translation = "error"
            for property_ in report.properties.values(): property_["status"] = "unknown"
            raise RuntimeError("source or tooling changed during verification; evidence is stale")
    except Unsupported as error:
        report.status = "unsupported"
        report.diagnostics.append(str(error))
    except subprocess.TimeoutExpired:
        report.status = "unknown"
        report.diagnostics.append("tooling timed out")
    except Exception as error:
        report.status = "error"
        report.diagnostics.append(f"{type(error).__name__}: {error}")
    status_path.write_text(json.dumps(asdict(report),indent=2,default=json_value)+"\n")
    if 'provenance' in locals() and (evidence/"recheck.py").exists():
        try: lean.seal(evidence, provenance["sources"], timeout)
        except (RuntimeError, OSError) as error:
            report.status = report.translation = "error"
            for property_ in report.properties.values(): property_["status"] = "unknown"
            report.diagnostics.append(str(error))
            status_path.write_text(json.dumps(asdict(report),indent=2,default=json_value)+"\n")
    return report
