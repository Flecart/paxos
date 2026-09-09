"""Compile the generated Python AST through upstream, then export actual RM terms."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def load_node():
    spec = importlib.util.spec_from_file_location("generated_node", ROOT / "generated" / "node.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Node


def compile_rm():
    # The analyzer uses sets in SSA merging. A fixed seed makes term order reproducible.
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve())],
                  dict(os.environ, PYTHONHASHSEED="0"))
    import torch  # Load libtorch before the native RM extension.
    import zrth
    from zrth.analyzer import convert_method

    manifest = json.loads((ROOT / "generated" / "manifest.json").read_text())
    upstream = ROOT / ".cache" / "reactive-modules"
    if not Path(zrth.__file__).resolve().is_relative_to(upstream.resolve()):
        raise RuntimeError("Expected the pinned editable compiler; run formal/bootstrap.py")
    actual_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    if actual_commit != manifest["rm_commit"]:
        raise RuntimeError("Upstream revision differs from the manifest; bootstrap and regenerate")
    changed = subprocess.check_output(
        ["git", "status", "--porcelain", "--", "python/zrth"], cwd=upstream, text=True)
    if changed:
        raise RuntimeError("Compiler sources have uncommitted changes; commit and pin them before export")
    Node = load_node()
    names = list(manifest["initial"])
    inputs = manifest["inputs"]
    wires = {name: zrth.Var(zrth.Int([1, 1])) for name in names + inputs}
    reset = convert_method(Node.reset, wires, [], cls=Node, builder=zrth.LIATermBuilder(), strict=True)
    step = convert_method(Node.step, wires, [], cls=Node, builder=zrth.LIATermBuilder(), strict=True)
    rm = zrth.Module(init=reset, update=step, vars=list(wires.values()))
    if set(rm.ctrl) != {wires[n] for n in names}:
        raise RuntimeError("RM controlled variables differ from the generated state schema")
    if not set(rm.extl) <= {wires[n] for n in inputs}:
        raise RuntimeError("RM has undeclared external variables")

    def export(terms):
        index = {wires[n]: i for i, n in enumerate(names + inputs)}
        rows = []
        for term in terms:
            op = type(term.itype).__name__
            reads = [index[w] for w in term.read]
            if len(term.write) != 1:
                raise ValueError("Only single-output scalar terms are supported")
            if term.write[0] in index:
                raise ValueError("Multiple writes to one wire")
            value = None
            match term.itype:
                case zrth.LIA.Int(t) | zrth.LIA.Bool(t):
                    if t.numel() != 1:
                        raise ValueError("Only scalar constants are supported")
                    value = int(t.item())
                case zrth.LIA.Id() | zrth.LIA.Add() | zrth.LIA.Sub() | zrth.LIA.Max() | zrth.LIA.Min() | zrth.LIA.Eq() | zrth.LIA.Ne() | zrth.LIA.Lt() | zrth.LIA.Le() | zrth.LIA.Gt() | zrth.LIA.Ge() | zrth.LIA.And() | zrth.LIA.Or() | zrth.LIA.Not() | zrth.LIA.Ite():
                    pass
                case _:
                    raise ValueError(f"Unsupported RM term; refusing opaque semantics: {term.itype}")
            index[term.write[0]] = len(names) + len(inputs) + len(rows)
            rows.append(dict(op=op, args=reads, value=value))
        outputs = [index[zrth.X(wires[n])] for n in names]
        return dict(terms=rows, outputs=outputs)

    atoms = list(rm.atoms)
    if len(atoms) != 1:
        raise ValueError("Expected one node atom")
    artifact = dict(format="paxos-rm-scalar-v1", state=names, inputs=inputs,
                    init=export(atoms[0].init), step=export(atoms[0].update),
                    rm_commit=manifest["rm_commit"], source_sha256=manifest["source_sha256"],
                    python_sha256=hashlib.sha256((ROOT / "generated" / "node.py").read_bytes()).hexdigest())
    artifact["unused_inputs"] = [n for n in inputs if wires[n] not in set(rm.extl)]
    path = ROOT / "generated" / "rm.json"
    path.write_text(json.dumps(artifact, separators=(",", ":")) + "\n")
    print(f"Upstream AST -> RM: {len(artifact['step']['terms'])} update terms, {len(names)} state fields")


if __name__ == "__main__":
    compile_rm()
