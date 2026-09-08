"""Compile the generated Python AST through upstream, then export actual RM terms."""
import hashlib
import importlib.util
import json
from pathlib import Path
import os
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

    class ScalarLIA(zrth.LIATermBuilder):
        # Pinned upstream builder.py:432 calls the nonexistent LIA.Const for
        # Booleans. Use the actual LIA.Bool constructor, without editing upstream.
        def const(self, tensor, output_wire=None):
            if tensor.dtype == torch.bool:
                tensor = tensor.reshape(1, 1)
                wire = output_wire if output_wire is not None else zrth.Wire(zrth.Bool([1, 1]))
                return zrth.Term.constant(zrth.LIA.Bool(tensor), [wire])
            return super().const(tensor, output_wire=output_wire)

    manifest = json.loads((ROOT / "generated" / "manifest.json").read_text())
    Node = load_node()
    names = list(manifest["initial"])
    inputs = manifest["inputs"]
    wires = {name: zrth.Var(zrth.Int([1, 1])) for name in names + inputs}
    reset = convert_method(Node.reset, wires, [], cls=Node, builder=ScalarLIA())
    step = convert_method(Node.step, wires, [], cls=Node, builder=ScalarLIA())
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
