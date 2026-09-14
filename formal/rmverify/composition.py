"""Direct Lean RM composition with independent atoms and complete round semantics."""
from dataclasses import asdict
from graphlib import TopologicalSorter, CycleError
from itertools import product
import hashlib
import inspect
import json
import re
from pathlib import Path
import subprocess
import tempfile
from textwrap import indent

from .api import Await, Choice, Report
from .value_types import mutable, typed, parts, data, matches
from .checking import function_id, provenance
from .execution import execute
from .frontend import (Unsupported, annotation, fields_of, method_program,
                       parameters, predicate_program, referenced_programs, domain_program)
from . import lean_backend as lean
from .lean_backend import state_cases


def prepare_model(spec):
    fields = fields_of(spec.target, require_init=False)
    if not spec.components or not spec.invariants:
        raise Unsupported("composition needs components and at least one invariant")
    model = dict(fields=fields, programs=[], atoms=[], invariants=[], relations=[], domains=[])
    names = list(fields)
    owners = {}
    for i, component in enumerate(spec.components):
        local = fields_of(component.target)
        if set(component.controls) != set(local):
            raise Unsupported("bind every local field to exactly one controlled variable")
        for field, variable in component.controls.items():
            if variable not in fields or fields[variable] != local[field]:
                raise Unsupported(f"unknown or ill-typed controlled variable: {variable}")
            if variable in owners:
                raise Unsupported(f"multiple controllers for {variable}")
            owners[variable] = i
    if set(owners) != set(fields):
        raise Unsupported("v2 requires a closed composition: every state variable needs a controller")

    def add(program):
        model["programs"].append(program)
        return len(model["programs"]) - 1

    ghosts = [i for i,c in enumerate(spec.components) if c.ghost]
    if len(ghosts)>1: raise Unsupported("use one deterministic observer component for ghost history")
    if ghosts and len(ghosts)==len(spec.components): raise Unsupported("an observer requires executable components")
    dependencies = {}
    for i, component in enumerate(spec.components):
        if type(component.stutter) is not bool or type(component.ghost) is not bool:
            raise Unsupported("stutter and ghost must be Booleans")
        local = fields_of(component.target)
        controlled = [names.index(component.controls[n]) for n in local]
        atom = dict(name=f"{i}:{component.target.__qualname__}", component=i,
                    controls=controlled, reads=list(controlled), awaits=[],
                    initial=[], actions=[], stutter=component.stutter, ghost=component.ghost)
        init_params = parameters(component.target.__init__)[1:]
        if set(component.initial_inputs) - {p.name for p in init_params}:
            raise Unsupported("unknown initializer parameter")
        domains = []
        for p in init_params:
            kind = annotation(p.annotation,namespace=component.target.__init__.__globals__)
            domain = component.initial_inputs.get(p.name, (False, True) if kind == "bool" else ())
            if not isinstance(domain, (tuple, list)) or not domain:
                raise Unsupported("initializer arguments need a nonempty finite domain (Bool defaults to both values)")
            if any(not matches(v,kind) for v in domain):
                raise Unsupported("initializer domain type mismatch")
            domains.append(domain)
        count = 1
        for domain in domains:
            count *= len(domain)
        # ponytail: finite constructor expansion is capped; symbolic relational
        # initialization is the upgrade if large domains are actually needed.
        if count > 256:
            raise Unsupported("more than 256 constructor alternatives")
        for values in product(*domains):
            arguments = dict(zip((p.name for p in init_params), values))
            index = add(method_program(component.target.__init__, local, initialize=True,
                                       initialize_arguments=arguments))
            atom["initial"].append(dict(index=index, arguments=arguments))
        if not component.transitions or len(set(component.transitions)) != len(component.transitions):
            raise Unsupported("select distinct component transition methods")
        if component.ghost and (component.stutter or len(component.transitions)!=1 or len(atom["initial"])!=1):
            raise Unsupported("ghost observer must have one initializer, one transition, and stutter=False")
        used_ports = set()
        dependencies[i] = set()
        for f in component.transitions:
            if not inspect.isfunction(f) or f.__name__ == "__init__" or getattr(component.target, f.__name__, None) is not f:
                raise Unsupported("transitions must be methods of their component class")
            program = method_program(f, local)
            if program.result != "none":
                raise Unsupported("component transitions must return None; expose outputs as fields")
            ports = []
            for p, kind in zip(parameters(f)[1:], program.inputs[len(local):], strict=True):
                used_ports.add(p.name)
                if p.name not in component.inputs:
                    raise Unsupported(f"unbound input port: {p.name}")
                binding = component.inputs[p.name]
                if isinstance(binding, Choice):
                    if component.ghost: raise Unsupported("ghost observers cannot make environmental choices")
                    variable = binding.domain
                    if callable(variable):
                        domain=domain_program(variable,fields,spec.target)
                        if parts(domain.result)[0]!=kind:raise Unsupported("Choice domain element type mismatch")
                        reads=set()
                        def visit(e):
                            if not isinstance(e,tuple):return
                            if e and e[0]=="var" and e[1]<len(fields):reads.add(e[1])
                            for x in e:visit(x)
                        visit(domain.body)
                        if any(spec.components[owners[names[n]]].ghost for n in reads):raise Unsupported("executable choices cannot read ghost history")
                        index=add(domain);model["domains"].append(index)
                        ports.append(dict(domain=index,awaited=False,choice=True))
                        atom["reads"].extend(reads)
                        continue
                    if isinstance(variable,(tuple,list)):
                        if not all(matches(v,kind) for v in variable):raise Unsupported("Choice domain element type mismatch")
                        ports.append(dict(choices=list(variable),kind=kind,awaited=False,choice=True))
                        continue
                    if not isinstance(variable, str) or variable not in fields or not mutable(fields[variable]):
                        raise Unsupported("Choice domain must name a finite collection in the previous state")
                    if parts(fields[variable])[0] != kind:
                        raise Unsupported(f"choice element type mismatch: {p.name}")
                    if spec.components[owners[variable]].ghost and not component.ghost: raise Unsupported("executable choices cannot read ghost history")
                    slot = names.index(variable)
                    ports.append(dict(variable=slot, awaited=False, choice=True))
                    atom["reads"].append(slot)
                    continue
                awaited = isinstance(binding, Await)
                variable = binding.variable if awaited else binding
                if not isinstance(variable, str) or variable not in fields or fields[variable] != kind:
                    raise Unsupported(f"unknown or ill-typed input port: {p.name}")
                if spec.components[owners[variable]].ghost and not component.ghost: raise Unsupported("executable components cannot read ghost history")
                slot = names.index(variable)
                ports.append(dict(variable=slot, awaited=awaited))
                atom["awaits" if awaited else "reads"].append(slot)
                if awaited:
                    dependencies[i].add(owners[variable])
            atom["actions"].append(dict(index=add(program), ports=ports))
        if used_ports != set(component.inputs):
            raise Unsupported("unused input port binding")
        atom["reads"] = sorted(set(atom["reads"]))
        atom["awaits"] = sorted(set(atom["awaits"]))
        model["atoms"].append(atom)
    try:
        order = list(TopologicalSorter(dependencies).static_order())
    except CycleError as error:
        raise Unsupported("cyclic await dependency (including self-await) is not an RM composition") from error
    model["atoms"] = [model["atoms"][i] for i in order]
    for auxiliary, functions in ((False, spec.invariants), (True, spec.strengthening)):
        for f in functions:
            identifier = ("auxiliary:" if auxiliary else "invariant:") + f.__qualname__
            if any(p["identifier"] == identifier for p in model["invariants"]):
                raise Unsupported("duplicate property")
            model["invariants"].append(dict(identifier=identifier, auxiliary=auxiliary,
                index=add(predicate_program(f, fields, spec.target, ["state"]))))
    for name, function, kinds in (("initial", spec.initial_relation, ["state"]),
                                  ("step", spec.step_relation, ["state", "state"])):
        if function is not None:
            model["relations"].append(dict(name=name, identifier="relation:"+function.__qualname__,
                index=add(predicate_program(function, fields, spec.target, kinds))))
    model["programs"] = referenced_programs(model["programs"])
    model["backend"] = "typed" if (bool(ghosts) or bool(model["domains"]) or any(p.get("choice") for a in model["atoms"] for m in a["actions"] for p in m["ports"]) or any(typed(k) for p in model["programs"] for k in [*p.slots,p.result]) or any(p.helpers for p in model["programs"])) else "scalar"
    return model


def identity(spec, model):
    components = []
    for c in spec.components:
        components.append(dict(target=[c.target.__module__, c.target.__qualname__],
            initial=function_id(c.target.__init__), transitions=[function_id(f) for f in c.transitions],
            controls=c.controls, inputs={k: ({"domain_function":function_id(v.domain)} if isinstance(v,Choice) and callable(v.domain) else data(asdict(v)) if isinstance(v,(Await,Choice)) else v) for k,v in c.inputs.items()},
            initial_inputs=c.initial_inputs, stutter=c.stutter, ghost=c.ghost))
    result = dict(**provenance(model["programs"], [spec.target, *(c.target for c in spec.components)]),
        specification=dict(target=[spec.target.__module__, spec.target.__qualname__], components=components,
            invariants=[function_id(f) for f in spec.invariants], strengthening=[function_id(f) for f in spec.strengthening],
            initial_relation=function_id(spec.initial_relation), step_relation=function_id(spec.step_relation)))
    return json.loads(json.dumps(data(result)))  # Snapshot mutable specification mappings too.


def definitions(model):
    lines, names = lean.program_definitions(model)
    lines += ["open RMVerify.Reactive", "structure State where"]
    kinds = list(model["fields"].values())
    for i, k in enumerate(kinds):
        lines.append(f"  f{i} : {lean.kind(k)}")
    lines.append("  deriving Repr, DecidableEq")

    def projection(slots, state):
        return lean.lean_list(lean.encode(kinds[i], f"{state}.f{i}") for i in slots)

    lines.append(f"def encodeState (s : State) : List Int := {projection(range(len(kinds)), 's')}")
    names.append("encodeState")
    for i, atom in enumerate(model["atoms"]):
        ctrl = atom["controls"]
        before, after = projection(ctrl, "s"), projection(ctrl, "t")
        expressions = {}
        for initializer in atom["initial"]:
            expressions[initializer["index"]] = "[]"
        for action in atom["actions"]:
            values = [lean.encode(kinds[j], f"s.f{j}") for j in ctrl]
            values += [lean.encode(kinds[p["variable"]], f"{'t' if p['awaited'] else 's'}.f{p['variable']}") for p in action["ports"]]
            expressions[action["index"]] = lean.lean_list(values)
        for source in (False, True):
            def output(index):
                env = f"(environment {expressions[index]})"
                run = f"(source{index}.exec {env}).outputs {len(ctrl)}" if source else f"compiled{index} {env}"
                return f"({run}).take {len(ctrl)}"
            prefix = "sourceAtom" if source else "atom"
            initial = " ∨ ".join(f"({before} = {output(a['index'])})" for a in atom["initial"])
            alternatives = ([f"({after} = {before})"] if atom["stutter"] else [])
            alternatives += [f"({after} = {output(a['index'])})" for a in atom["actions"]]
            lines += [f"def {prefix}{i} : Atom State where",
                      f"  controls := {lean.lean_list(map(str, ctrl))}",
                      f"  reads := {lean.lean_list(map(str, atom['reads']))}",
                      f"  awaits := {lean.lean_list(map(str, atom['awaits']))}",
                      f"  initial s := {initial}", f"  step s t := {' ∨ '.join(alternatives)}"]
        lines += [f"theorem atom_agreement{i} : sourceAtom{i} = atom{i} := by"]
        for index, values in expressions.items():
            env = f"(environment {values})"
            binders = " ".join(f"({v} : State)" for v in ("s", "t") if f"{v}." in values)
            lines += [f"  have agree{index} {binders} : (source{index}.exec {env}).outputs {len(ctrl)} = compiled{index} {env} := by",
                      f"    exact translation{index} _ (by simp [environment])"]
        lines += [f"  unfold sourceAtom{i} atom{i}", "  rw [Atom.mk.injEq]",
                  "  refine ⟨rfl, rfl, rfl, ?_, ?_⟩",
                  "  · funext s; apply propext",
                  "    simp only [" + ", ".join(f"agree{j}" for j in expressions) + "]",
                  "    all_goals", indent(lean.tactic(names), "      "),
                  "  · funext s t; apply propext",
                  "    simp only [" + ", ".join(f"agree{j}" for j in expressions) + "]",
                  "    all_goals", indent(lean.tactic(names), "      "), f"#print axioms atom_agreement{i}"]
        lines += [f"theorem atom_respects{i} : atom{i}.Respects (fun s => environment (encodeState s)) := by",
                  "  constructor",
                  "  · intro s t h", indent(lean.tactic(names+[f"atom{i}", "Atom.Respects", "AgreeOn"]), "    "),
                  "  · intro s s' t t' h₁ h₂", indent(lean.tactic(names+[f"atom{i}", "Atom.Respects", "AgreeOn"]), "    "),
                  f"#print axioms atom_respects{i}"]
        names.append(f"atom{i}")
    for source in (False, True):
        prefix = "sourceAtom" if source else "atom"
        for i in range(len(model["atoms"])):
            lines.append(f"def {'sourcePart' if source else 'part'}{i} : Reactive.Module State := ⟨[{prefix}{i}]⟩")
        parts = [f"{'sourcePart' if source else 'part'}{i}" for i in range(len(model["atoms"]))]
        composed = parts[0]
        for part in parts[1:]:
            composed = f"({composed}.parallel {part})"
        lines.append(f"def {'sourceModule' if source else 'composed'} : Reactive.Module State := {composed}")
    part_names = [f"part{i}" for i in range(len(model["atoms"]))]
    names += part_names + ["composed", "Reactive.Module.parallel", "Reactive.Module.initial", "Reactive.Module.step"]
    lines += ["theorem source_module_eq : sourceModule = composed := by",
              "  simp only [sourceModule, composed, " + ", ".join(part_names + [f"sourcePart{i}" for i in range(len(model["atoms"]))] + [f"atom_agreement{i}" for i in range(len(model["atoms"]))]) + "]",
              "theorem composition_correspondence (s t : State) : sourceModule.step s t ↔ composed.step s t := by rw [source_module_eq]",
              f"theorem well_formed : composed.wellFormed {len(kinds)} = true := by decide",
              "#print axioms source_module_eq", "#print axioms composition_correspondence", "#print axioms well_formed"]
    for i, prop in enumerate(model["invariants"]):
        j = prop["index"]
        lines += [f"def inv{i} (s : State) : Prop := environment (compiled{j} (environment (encodeState s))) 0 ≠ 0",
                  f"def sourceInv{i} (s : State) : Prop := environment ((source{j}.exec (environment (encodeState s))).outputs 0) 0 ≠ 0",
                  f"theorem inv_agreement{i} (s : State) : sourceInv{i} s ↔ inv{i} s := by",
                  f"  unfold sourceInv{i} inv{i}; rw [translation{j} _ (by simp [environment, encodeState])]",
                  f"#print axioms inv_agreement{i}"]
        names.append(f"inv{i}")
    for source in (False, True):
        inv, safe = ("sourceInv", "sourceSafe") if source else ("inv", "safe")
        lines.append(f"def {safe} (s : State) : Prop := " + " ∧ ".join([f"{inv}{i} s" for i in range(len(model["invariants"]))]+["True"]))
    names.append("safe")
    for relation in model["relations"]:
        args = "(s : State)" if relation["name"] == "initial" else "(s t : State)"
        values = "encodeState s" if relation["name"] == "initial" else "encodeState s ++ encodeState t"
        j, name = relation["index"], relation["name"]
        lines += [f"def specified_{name} {args} : Prop := environment (compiled{j} (environment ({values}))) 0 ≠ 0",
                  f"def source_specified_{name} {args} : Prop := environment ((source{j}.exec (environment ({values}))).outputs 0) 0 ≠ 0",
                  f"theorem specified_{name}_agreement {args} : source_specified_{name} s {'t' if name == 'step' else ''} ↔ specified_{name} s {'t' if name == 'step' else ''} := by",
                  f"  unfold source_specified_{name} specified_{name}; rw [translation{j} _ (by simp [environment, encodeState])]",
                  f"#print axioms specified_{name}_agreement"]
        names.append(f"specified_{name}")
    # Construct one complete round in await order; stuttering is per atom.
    initial_values, next_values = {}, {}
    witness_names = []
    for i, atom in enumerate(model["atoms"]):
        initial = atom["initial"][0]["index"]
        lines.append(f"def initialOutput{i} : List Int := (compiled{initial} (environment [])).take {len(atom['controls'])}")
        values = [lean.encode(kinds[j], f"s.f{j}") for j in atom["controls"]]
        if atom["stutter"]:
            output = lean.lean_list(values)
        else:
            action = atom["actions"][0]
            values += [lean.encode(kinds[p["variable"]], next_values[p["variable"]] if p["awaited"] else f"s.f{p['variable']}") for p in action["ports"]]
            output = f"(compiled{action['index']} (environment {lean.lean_list(values)})).take {len(atom['controls'])}"
        lines.append(f"def nextOutput{i} (s : State) : List Int := {output}")
        for j, slot in enumerate(atom["controls"]):
            initial_values[slot] = lean.decode(kinds[slot], f"environment initialOutput{i} {j}")
            next_values[slot] = lean.decode(kinds[slot], f"environment (nextOutput{i} s) {j}")
        witness_names += [f"initialOutput{i}", f"nextOutput{i}"]
    lines += ["def initialWitness : State := ⟨" + ", ".join(initial_values[i] for i in range(len(kinds))) + "⟩",
              "def nextWitness (s : State) : State := ⟨" + ", ".join(next_values[i] for i in range(len(kinds))) + "⟩",
              "theorem initial_nonempty : ∃ s, composed.initial s := by",
              "  refine ⟨initialWitness, ?_⟩", indent(lean.tactic(names+witness_names+["initialWitness"]), "  "),
              "theorem nonblocking (s : State) : ∃ t, composed.step s t := by",
              "  refine ⟨nextWitness s, ?_⟩", indent(lean.tactic(names+witness_names+["nextWitness"]), "  "),
              "#print axioms initial_nonempty", "#print axioms nonblocking"]
    lines.append("end Verified")
    source = "\n".join(lines)+"\n"
    for i, name in reversed(list(enumerate(model["fields"]))):
        source = re.sub(rf"\bf{i}\b", "«" + name + "»", source)
    return source, names


def invariant_proof(model, names):
    # Normalize hypotheses independently first. Contextual simplification of
    # the relational equalities can discard arithmetic premises needed later.
    lines = ["import Translation", "set_option veil.smt.trust false", "set_option linter.all false", "open RMVerify RMVerify.Reactive Verified",
             "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 2000000",
             "theorem invariant : ∀ s, Reactive.Reachable composed s → safe s := by",
             "  apply Reactive.invariant_of_induction",
             "  · intro s hs", indent(state_cases(model, ["s"]), "    "), "    all_goals", indent(lean.tactic(names, contextual=False), "      "),
             "  · intro s t hs ht", indent(state_cases(model, ["s", "t"]), "    "), "    all_goals", indent(lean.tactic(names, contextual=False), "      "),
             "theorem always_safe (states : Nat → State) (start : composed.initial (states 0))",
             "    (round : ∀ n, composed.step (states n) (states (n+1))) : ∀ n, safe (states n) :=",
             "  Reactive.invariant_always composed safe invariant states start round",
             "theorem source_invariant : ∀ s, Reactive.Reachable sourceModule s → sourceSafe s := by",
             "  simpa only [source_module_eq, sourceSafe, safe, " + ", ".join(f"inv_agreement{i}" for i in range(len(model["invariants"]))) + "] using invariant",
             "theorem veil_invariant : ∀ s, composed.toVeil.reachable () s → safe s := by",
             "  intro s h; exact invariant s ((Reactive.veil_reachable composed s).mp h)",
             "#print axioms veil_invariant",
             "#print axioms invariant", "#print axioms always_safe", "#print axioms source_invariant"]
    return "\n".join(lines)+"\n"



def relation_proof(relation, names):
    name = relation["name"]
    binders, args = ("(s : State)", "s") if name == "initial" else ("(s t : State)", "s t")
    return "\n".join(["import Translation", "set_option veil.smt.trust false", "set_option linter.all false", "open RMVerify RMVerify.Reactive Verified",
        "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 2000000",
        f"theorem relation {binders} : composed.{name} {args} ↔ specified_{name} {args} := by",
        "  cases s" + ("; cases t" if name == "step" else ""), indent(lean.tactic(names), "  "),
        f"theorem source_relation {binders} : sourceModule.{name} {args} ↔ source_specified_{name} {args} := by",
        f"  simpa only [source_module_eq, specified_{name}_agreement] using relation {args}",
        "#print axioms relation", "#print axioms source_relation", ""])


def differential(spec, model):
    """Executable checks supplement the universal component translation proofs."""
    count = 0
    for atom in model["atoms"]:
        component = spec.components[atom["component"]]
        # Local field order is the source declaration order, not binding order.
        local = list(fields_of(component.target))
        for init in atom["initial"]:
            obj = component.target(*init["arguments"].values())
            actual = [getattr(obj, name) for name in local] + [0]
            if actual != execute(model["programs"][init["index"]], []):
                raise ValueError("constructor translation mismatch")
            count += 1
        for action in atom["actions"]:
            p = model["programs"][action["index"]]
            domains = [(False, True) if k == "bool" else (-1, 0, 1, 2, 3) for k in p.inputs]
            from itertools import islice
            for values in islice(product(*domains), 128):
                obj = object.__new__(component.target)
                for name, value in zip(local, values):
                    setattr(obj, name, value)
                result = p.function(obj, *values[len(local):])
                actual = [getattr(obj, name) for name in local] + [0]
                if result is not None or actual != execute(model["programs"][action["index"]], list(values)):
                    raise ValueError("component translation mismatch")
                count += 1
    return count


def initial_states(model):
    """All finite constructor alternatives."""
    states = {tuple(0 for _ in model["fields"])}
    for atom in model["atoms"]:
        states = {tuple(dict(zip(atom["controls"], values)).get(i, old[i]) for i in range(len(old)))
                  for old in states for a in atom["initial"]
                  for values in [execute(model["programs"][a["index"]], [])[:-1]]}
    return states


def successors(model, state):
    """Execute a complete round, retaining old reads across all subrounds."""
    if len(state) != len(model["fields"]):
        raise ValueError("state arity mismatch")
    candidates = {tuple(state)}
    for atom in model["atoms"]:
        updated = set()
        for candidate in candidates:
            if atom["stutter"]:
                updated.add(candidate)
            for action in atom["actions"]:
                values = [state[j] for j in atom["controls"]]
                values += [(candidate if p["awaited"] else state)[p["variable"]] for p in action["ports"]]
                writes = dict(zip(atom["controls"], execute(model["programs"][action["index"]], values)[:-1], strict=True))
                updated.add(tuple(writes.get(i, value) for i,value in enumerate(candidate)))
        candidates = updated
    return candidates


def witness_proof(witness, names):
    lines = ["import Translation", "set_option veil.smt.trust false", "set_option linter.all false", "open RMVerify RMVerify.Reactive Verified",
             "set_option maxRecDepth 100000", "set_option maxHeartbeats 2000000"]
    for i, state in enumerate(witness["states"]):
        lines.append(f"def state{i} : State := ⟨" + ", ".join(lean.value(v) for v in state) + "⟩")
    if witness["kind"] == "relation_mismatch":
        relation = witness["relation"]
        args = "state0" if relation == "initial" else "state0 state1"
        binders, variables = ("(s : State)", "s") if relation == "initial" else ("(s t : State)", "s t")
        lines += [f"theorem mismatch : ¬ (composed.{relation} {args} ↔ specified_{relation} {args}) := by decide",
                  f"theorem refutation : ¬ (∀ {binders}, composed.{relation} {variables} ↔ specified_{relation} {variables}) := by",
                  f"  intro h; exact mismatch (h {args})",
                  f"theorem source_refutation : ¬ (∀ {binders}, sourceModule.{relation} {variables} ↔ source_specified_{relation} {variables}) := by",
                  f"  simpa only [source_module_eq, specified_{relation}_agreement] using refutation"]
    else:
        lines += ["theorem reach0 : Reactive.Reachable composed state0 := .initial (by decide)"]
        n = len(witness["states"]) - 1
        for i in range(n):
            lines.append(f"theorem reach{i+1} : Reactive.Reachable composed state{i+1} := .step reach{i} (by decide)")
        j = witness["invariant"]
        lines += [f"theorem bad : ¬ inv{j} state{n} := by decide",
                  f"theorem refutation : ¬ (∀ s, Reactive.Reachable composed s → inv{j} s) := by",
                  f"  intro h; exact bad (h state{n} reach{n})",
                  f"theorem source_refutation : ¬ (∀ s, Reactive.Reachable sourceModule s → sourceInv{j} s) := by",
                  f"  simpa only [source_module_eq, inv_agreement{j}] using refutation"]
    lines += ["#print axioms refutation", "#print axioms source_refutation"]
    proof = "by\n" + indent(lean.tactic(names + [f"state{i}" for i in range(len(witness["states"]))]), "  ")
    return ("\n".join(lines) + "\n").replace("by decide", proof)


def verify(spec, *, directory=None, timeout=60, depth=10):
    if timeout <= 0 or depth < 0:
        raise ValueError("timeout must be positive and depth nonnegative")
    parent = Path(directory or ".rmverify").resolve()
    parent.mkdir(parents=True, exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix="compose-", dir=parent))
    report = Report("error", evidence=str(evidence))
    try:
        model = prepare_model(spec)
        origin = identity(spec, model)
        backend = __import__(__package__ + ".typed_composition", fromlist=["*"]) if model["backend"] == "typed" else __import__(__name__, fromlist=["*"])
        artifact = dict(**origin, version=4, pipeline="Python → Lean RM definitions → checked theorem", fields=model["fields"], atoms=model["atoms"],
            invariants=model["invariants"], relations=model["relations"],
            programs=[{k: v for k,v in vars(p).items() if k not in ("function", "helpers")} for p in model["programs"]])
        artifact["sha256"] = hashlib.sha256(json.dumps(data(artifact), sort_keys=True).encode()).hexdigest()
        (evidence / "artifact.json").write_text(json.dumps(data(artifact), indent=2)+"\n")
        for p in model["invariants"] + model["relations"]:
            report.properties[p["identifier"]] = dict(status="unknown")
        if model["backend"] == "typed": report.properties["no-fault"] = dict(status="unknown")
        lean.prepare(evidence)
        lean.build(evidence, timeout, typed=model["backend"] == "typed")
        source, names = backend.definitions(model)
        audits = ([f"Verified.translation{i}" for i in range(len(model["programs"]))]
                  + [name for i in range(len(model["atoms"])) for name in (f"Verified.atom_agreement{i}", f"Verified.atom_respects{i}")]
                  + [f"Verified.inv_agreement{i}" for i in range(len(model["invariants"]))]
                  + [f"Verified.specified_{r['name']}_agreement" for r in model["relations"]]
                  + ["Verified.source_module_eq", "Verified.composition_correspondence", "Verified.well_formed",
                     "Verified.initial_nonempty", "Verified.nonblocking"])
        if model["backend"] == "typed": audits += backend.extra_audits(model)
        report.translation, reason = lean.run(evidence, "Translation", source, audits, timeout, output=True)
        report.status = report.translation
        if reason:
            report.diagnostics.append(reason)
        if report.translation == "proved":
            report.diagnostics.append(f"{backend.differential(spec, model)} Python/source probes passed (regression evidence only)")
            status, reason = lean.run(evidence, "Invariants", backend.invariant_proof(model, names),
                                     ["invariant", "always_safe", "source_invariant", "veil_invariant"], timeout)
            for p in model["invariants"]:
                report.properties[p["identifier"]] = dict(status=status)
            if model["backend"] == "typed": report.properties["no-fault"] = dict(status=status)
            if reason:
                report.diagnostics.append(reason)
            if model["backend"] == "typed" and status != "proved":
                healthy,reason=lean.run(evidence,"NoFault",backend.no_fault_proof(model,names),["invariant","source_invariant"],timeout)
                report.properties["no-fault"]=dict(status=healthy)
                if reason:report.diagnostics.append(reason)
            for r in model["relations"]:
                status, reason = lean.run(evidence, r["name"].capitalize()+"Relation", backend.relation_proof(r, names),
                                         ["relation", "source_relation"], timeout)
                report.properties[r["identifier"]] = dict(status=status)
                if reason:
                    report.diagnostics.append(reason)
            unresolved = {key for key, p in report.properties.items() if p["status"] == "unknown"}
            if unresolved.intersection(p["identifier"] for p in model["invariants"]):
                from .symbolic import search
                for query in search(evidence,model,names,composition=True,typed=model["backend"]=="typed",depth=depth,timeout=timeout):
                    report.diagnostics.append(f"Veil {query['kind']}: {query['status']} (diagnostic only; {query['log']})")
            if unresolved:
                from .solver import composition_counterexamples
                if model["backend"] == "typed": composition_counterexamples = backend.counterexamples
                for identifier, witness in composition_counterexamples(model, depth, timeout, unresolved).items():
                    name = "Witness" + str(list(report.properties).index(identifier))
                    (evidence/f"{name}.json").write_text(json.dumps(data(witness), indent=2)+"\n")
                    status, reason = lean.run(evidence, name, backend.witness_proof(witness, names, model) if model["backend"] == "typed" else witness_proof(witness, names),
                                             ["refutation", "source_refutation"], timeout)
                    if status == "proved":
                        report.properties[identifier] = dict(status="refuted", witness=witness)
                    elif reason:
                        report.diagnostics.append(reason)
            statuses = {p["status"] for p in report.properties.values()}
            report.status = "error" if "error" in statuses else "refuted" if "refuted" in statuses else "unknown" if "unknown" in statuses else "proved"
        if identity(spec, model) != origin:
            report.translation = "error"
            for p in report.properties.values():
                p["status"] = "unknown"
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
    (evidence / "report.json").write_text(json.dumps(data(report), indent=2)+"\n")
    if 'origin' in locals() and (evidence/"recheck.py").exists():
        try: lean.seal(evidence, origin["sources"], timeout)
        except (RuntimeError, OSError) as error:
            report.status = report.translation = "error"
            for property_ in report.properties.values(): property_["status"] = "unknown"
            report.diagnostics.append(str(error))
            (evidence/"report.json").write_text(json.dumps(data(report), indent=2)+"\n")
    return report
