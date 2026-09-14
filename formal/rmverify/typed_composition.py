"""Typed relational atoms: finite choices, explicit faults, complete RM rounds."""
from copy import deepcopy
from itertools import product, islice
from textwrap import indent
import json
import re
from . import typed_backend as typed
from . import lean_backend as lean
from .frontend import Unsupported, fields_of
from .execution import execute, ExecutionFault
from .value_types import parts, default_value, probes, data


def projection(model, atom, state):
    fields = list(model['fields'])
    return [f'{state}.«{fields[n]}»' for n in atom['controls']] + [f'{state}.«$fault{atom["component"]}»']


def tuple_(values):
    return '('+', '.join(values)+')'


def definitions(model):
    lines,names = typed.program_definitions(model)
    lines.insert(0,"import Network")
    fields=list(model['fields']); kinds=list(model['fields'].values())
    faults=[f'$fault{i}' for i in range(len(model['atoms']))]
    lines += ['open RMVerify.Reactive', 'structure State where']
    lines += [f'  «{n}» : {typed.kind(k)}' for n,k in model['fields'].items()]
    lines += [f'  «{n}» : Option Fault' for n in faults]+['  deriving Repr, DecidableEq']
    lines += ['inductive Coordinate where']
    for i,k in enumerate(kinds): lines += [f'  | c{i} (value : {typed.kind(k)})']
    lines += ['  | fault (value : Option Fault)', '  | absent', '  deriving DecidableEq', 'def coordinate (s : State) : Nat → Coordinate']
    for i,n in enumerate(fields): lines += [f'  | {i} => .c{i} s.«{n}»']
    for i,n in enumerate(faults): lines += [f'  | {len(fields)+i} => .fault s.«{n}»']
    lines += ['  | _ => .absent']
    domain_names=[]
    for i in model['domains']:
        p=model['programs'][i]; values=[f's.«{n}»' for n in fields]
        for source in (False,True):
            frame=(typed.source_frame_value if source else typed.frame_value)(p,values)
            run=f'source{i}.exec ({frame})' if source else f'compiled{i} ({frame})'
            result=f'(({run}).toExcept []).toOption.getD []'
            if p.result.startswith('dict['):result=f'({result}).map Prod.fst'
            lines += [f'def {"sourceDomain" if source else "domain"}{i} (s : State) : List ({typed.kind(parts(p.result)[0])}) := {result}']
        lines += [f'theorem domain_agreement{i} : sourceDomain{i} = domain{i} := by funext s; simp only [sourceDomain{i}, domain{i}, translation{i}]',
                  f'theorem domain_total{i} (s : State) : ∃ f xs, source{i}.exec ({typed.source_frame_value(p,values)}) = .returned f xs := by',indent(typed.tactic(names),'  '),f'#print axioms domain_agreement{i}',f'#print axioms domain_total{i}']
        domain_names += [f'domain{i}']
    names += domain_names
    bridges=[]; atom_names=[]
    for ai,atom in enumerate(model['atoms']):
        controls=atom['controls']; fault=len(fields)+atom['component']
        allctrl=controls+[fault]
        expressions={}
        for init in atom['initial']: expressions[init['index']]=[]
        for action in atom['actions']:
            expressions[action['index']]=[f's.«{fields[n]}»' for n in controls]+[
                f'a{j}' if p.get('choice') else f'{"t" if p["awaited"] else "s"}.«{fields[p["variable"]]}»'
                for j,p in enumerate(action['ports'])]
        for index,values in expressions.items():
            p=model['programs'][index]
            resulttype='('+' × '.join([typed.kind(kinds[n]) for n in controls]+['Option Fault'])+')'
            for source in (False,True):
                prefix='sourceOutput' if source else 'output'
                projected=[f'o.frame.v{n}' for n in range(len(controls))]+['o.fault?']
                lines += [f'def {prefix}{index} (o : Outcome Frame{index} {typed.kind(p.result)}) : {resulttype} := {tuple_(projected)}']
            lines += [f'theorem output_agreement{index} : sourceOutput{index} = output{index} := by funext o; cases o <;> rfl',f'#print axioms output_agreement{index}']
            bridges += [f'output_agreement{index}']
            names += [f'output{index}']
        for source in (False,True):
            prefix='sourceAtom' if source else 'atom'
            def output(index):
                p=model['programs'][index]
                builder=typed.source_frame_value if source else typed.frame_value
                frame=builder(p,expressions[index])
                run=f'source{index}.exec ({frame})' if source else f'compiled{index} ({frame})'
                return f'{"sourceOutput" if source else "output"}{index} ({run})'
            before,after=tuple_(projection(model,atom,'s')),tuple_(projection(model,atom,'t'))
            initial=' ∨ '.join(f'{before} = {output(a["index"])}' for a in atom['initial'])
            alternatives=[f'{after} = {before}'] if atom['stutter'] else []
            for action in atom['actions']:
                claim=f'{after} = {output(action["index"])}'
                for j,p in reversed(list(enumerate(action['ports']))):
                    if p.get('choice'):
                        if 'domain' in p:domain=f'{"sourceDomain" if source else "domain"}{p["domain"]} s'
                        elif 'choices' in p:domain='['+', '.join(typed.value(v,p['kind']) for v in p['choices'])+']'
                        else:
                            domain=f's.«{fields[p["variable"]]}»'
                            if kinds[p['variable']].startswith('dict['): domain=f'({domain}.map Prod.fst)'
                        claim=f'∃ a{j} ∈ {domain}, {claim}'
                alternatives.append('('+claim+')')
            faultname=f's.«$fault{atom["component"]}»'
            step=f'if {faultname}.isSome then {after} = {before} else ('+' ∨ '.join(alternatives)+')'
            lines += [f'def {prefix}{ai} : Atom State where',f'  controls := {allctrl}',f'  reads := {atom["reads"]}',f'  awaits := {atom["awaits"]}',f'  initial s := {initial}',f'  step s t := {step}']
        agreements=[f'domain_agreement{i}' for i in model['domains']]+[f'translation{i}' for i in expressions]+[f'output_agreement{i}' for i in expressions]
        lines += [f'theorem atom_agreement{ai} : sourceAtom{ai} = atom{ai} := by',
                  f'  simp only [sourceAtom{ai}, atom{ai}, '+', '.join(agreements)+']',f'#print axioms atom_agreement{ai}']
        lines += [f'theorem atom_respects{ai} : atom{ai}.Respects coordinate := by',
                  '  constructor','  · intro s t h',f'    simp [AgreeOn, atom{ai}, coordinate] at h',
                  f'    simp only [atom{ai}]; rcases h with '+tuple_([f'h{j}' for j in range(len(allctrl))]).replace('(','⟨').replace(')','⟩'),
                  '    simp_all'+(' ['+', '.join(names)+']' if model['domains'] else ''),
                  '  · intro s s\' t t\' h₁ h₂',f'    simp [AgreeOn, atom{ai}, coordinate] at h₁ h₂',
                  f'    simp only [atom{ai}]', '    simp_all'+(' ['+', '.join(names)+']' if model['domains'] else ''),f'#print axioms atom_respects{ai}']
        atom_names.append(f'atom{ai}')
    for source in (False,True):
        prefix='sourceAtom' if source else 'atom'; name='sourceModule' if source else 'composed'
        lines += [f'def {name} : Reactive.Module State := ⟨['+', '.join(f'{prefix}{i}' for i in range(len(model['atoms'])))+']⟩']
    lines += ['theorem source_module_eq : sourceModule = composed := by',
              '  simp only [sourceModule, composed, '+', '.join(f'atom_agreement{i}' for i in range(len(model['atoms'])))+']',
              'theorem composition_correspondence (s t : State) : sourceModule.step s t ↔ composed.step s t := by rw [source_module_eq]',
              f'theorem well_formed : composed.wellFormed {len(fields)+len(faults)} = true := by decide',
              '#print axioms source_module_eq','#print axioms composition_correspondence','#print axioms well_formed']
    names += atom_names+['composed','Reactive.Module.initial','Reactive.Module.step']
    for j,prop in enumerate(model['invariants']):
        i=prop['index']; p=model['programs'][i]; values=[f's.«{n}»' for n in fields]
        lines += [f'def inv{j} (s : State) : Prop := ∃ f, compiled{i} ({typed.frame_value(p,values)}) = .returned f true',
                  f'def sourceInv{j} (s : State) : Prop := ∃ f, source{i}.exec ({typed.source_frame_value(p,values)}) = .returned f true',
                  f'theorem inv_agreement{j} (s : State) : sourceInv{j} s ↔ inv{j} s := by simp only [sourceInv{j}, inv{j}, translation{i}]',f'#print axioms inv_agreement{j}']
        names += [f'inv{j}']
    for source in (False,True):
        prefix='source' if source else ''
        clauses=[f's.«{n}» = none' for n in faults]+[f'{"sourceInv" if source else "inv"}{j} s' for j in range(len(model['invariants']))]+['True']
        lines += [f'def {"sourceSafe" if source else "safe"} (s : State) : Prop := '+' ∧ '.join(clauses)]
    lines += ['theorem safe_agreement (s : State) : sourceSafe s ↔ safe s := by simp only [sourceSafe, safe, '+', '.join(f'inv_agreement{i}' for i in range(len(model['invariants'])))+']','#print axioms safe_agreement']
    names += ['safe']
    lines += ['def regular (s : State) : Prop := '+' ∧ '.join([f's.«{n}» = none' for n in faults]+['True'])]
    names += ['regular']
    for r in model['relations']:
        i,name=r['index'],r['name']; p=model['programs'][i]; args='s' if name=='initial' else 's t'
        values=[f'{s}.«{n}»' for s in (['s'] if name=='initial' else ['s','t']) for n in fields]
        for source in (False,True):
            frame=(typed.source_frame_value if source else typed.frame_value)(p,values)
            run=f'source{i}.exec ({frame})' if source else f'compiled{i} ({frame})'
            lines += [f'def {"source_" if source else ""}specified_{name} ({args} : State) : Prop := ∃ f, {run} = .returned f true']
        lines += [f'theorem specified_{name}_agreement ({args} : State) : source_specified_{name} {args} ↔ specified_{name} {args} := by simp only [source_specified_{name}, specified_{name}, translation{i}]',f'#print axioms specified_{name}_agreement']
        names += [f'specified_{name}']
    # Construct an inhabitant by selecting one initializer per atom, and one
    # non-choice alternative where stuttering is disabled, in await order.
    initial_values={}; next_values={}; witness_names=[]
    for ai,atom in enumerate(model['atoms']):
        index=atom['initial'][0]['index']; p=model['programs'][index]
        lines += [f'def initialOutput{ai} := output{index} (compiled{index} ({typed.frame_value(p,[])}))']
        before=tuple_(projection(model,atom,'s'))
        if atom['stutter']: output=before
        else:
            action=next((a for a in atom['actions'] if not any(p.get('choice') for p in a['ports'])),None)
            if action is None: raise Unsupported('a possibly empty Choice domain requires stutter or an unconditional action')
            index=action['index']; p=model['programs'][index]
            values=[f's.«{fields[n]}»' for n in atom['controls']]+[next_values[fields[port['variable']]] if port['awaited'] else f's.«{fields[port["variable"]]}»' for port in action['ports']]
            output=f'if s.«$fault{atom["component"]}».isSome then {before} else output{index} (compiled{index} ({typed.frame_value(p,values)}))'
        lines += [f'def nextOutput{ai} (s : State) := {output}']
        coords=[fields[n] for n in atom['controls']]+[f'$fault{atom["component"]}']
        for j,n in enumerate(coords):
            suffix='.2'*j+('.1' if j<len(coords)-1 else '')
            initial_values[n]=f'initialOutput{ai}{suffix}';next_values[n]=f'(nextOutput{ai} s){suffix}'
        witness_names += [f'initialOutput{ai}',f'nextOutput{ai}']
    for label,values in [('initialWitness',initial_values),('nextWitness (s : State)',next_values)]:
        lines += [f'def {label} : State := {{'+', '.join(f'«{n}» := {values[n]}' for n in fields+faults)+'}']
    for theorem,claim,witness in [('initial_nonempty','∃ s, composed.initial s','initialWitness'),('nonblocking (s : State)','∃ t, composed.step s t','nextWitness s')]:
        lines += [f'theorem {theorem} : {claim} := by',f'  refine ⟨{witness}, ?_⟩']
        if theorem.startswith('nonblocking'):
            for j in range(len(model['atoms'])):lines += [f'  all_goals by_cases hf{j} : s.«$fault{j}».isSome = true']
        structural=atom_names+['composed','Reactive.Module.initial','Reactive.Module.step']+witness_names+['initialWitness','nextWitness']
        lines += ['  all_goals simp_all (config := {failIfUnchanged := false}) ['+', '.join(structural)+']','  all_goals grind',f'#print axioms {theorem.split()[0]}']
    observer_lines, _ = observer_definitions(model)
    lines += observer_lines
    lines += ['end Verified']
    return re.sub(r'(?<!\w)\.ok\b','Except.ok','\n'.join(lines)+'\n'),names


def extra_audits(model):
    return ([f'Verified.{n}{i}' for i in model['domains'] for n in ('domain_agreement','domain_total')]+['Verified.'+n for n in observer_definitions(model)[1]]+['Verified.safe_agreement']+[f'Verified.{n}{i}_{j}' for i,p in enumerate(model['programs']) for j,_ in enumerate(typed.set_loops(p)) for n in ('set_loop_commutes','set_loop_order')]+[f'Verified.{n}{i}' for i in range(len(model['programs'])) for n in ('ownership','affine')]
        +[f'Verified.output_agreement{a["index"]}' for atom in model['atoms'] for a in atom['initial']+atom['actions']]
        +[f'Verified.{n}{i}_{j}' for i,p in enumerate(model['programs']) for j,_ in enumerate(typed.set_quantifiers(p)) for n in ('set_total','set_order')])


def invariant_proof(model,names):
    lines=['import Translation','set_option veil.smt.trust false','open RMVerify RMVerify.TypedSource RMVerify.Reactive Verified','set_option maxRecDepth 100000','set_option maxHeartbeats 8000000','set_option linter.all false',
           'theorem invariant : ∀ s, Reactive.Reachable composed s → safe s := by',
           '  apply Reactive.invariant_of_induction','  · intro s hs', '    simp only [composed, Reactive.Module.initial, List.forall_mem_cons, List.forall_mem_nil, and_true] at hs', '    simp ['+', '.join([f'atom{i}' for i in range(len(model['atoms']))]+[n for atom in model['atoms'] for a in atom['initial'] for n in (f'output{a["index"]}',f'compiled{a["index"]}',f'«{model["programs"][a["index"]].function.__qualname__}_{a["index"]}»')])+', '+typed.REDUCE+'] at hs', indent(typed.tactic(names,contextual=False),'    '),
           '  · intro s t hs ht']
    # Keep atom alternatives relational; grind splits only relevant cases.
    options=[]
    for j,(n,k) in enumerate(model['fields'].items()):
        if k.startswith('option['):
            lines += [f'    all_goals cases h{j} : s.«{n}» <;> cases hnew{j} : t.«{n}»']
            options += [f'h{j}',f'hnew{j}']
    lines += ['    all_goals',indent(typed.tactic(options+names,contextual=False),'      '),
           'theorem always_safe (states : Nat → State) (start : composed.initial (states 0))',
           '    (round : ∀ n, composed.step (states n) (states (n+1))) : ∀ n, safe (states n) :=',
           '  Reactive.invariant_always composed safe invariant states start round',
           'theorem source_invariant : ∀ s, Reactive.Reachable sourceModule s → sourceSafe s := by simpa only [source_module_eq, safe_agreement] using invariant',
           'theorem veil_invariant : ∀ s, composed.toVeil.reachable () s → safe s := by',
           '  intro s h; exact invariant s ((Reactive.veil_reachable composed s).mp h)']
    lines += [f'#print axioms {n}' for n in ('invariant','always_safe','source_invariant','veil_invariant')]
    return '\n'.join(line.replace('splits := 64','splits := 128') for line in '\n'.join(lines).splitlines() if "repeat'" not in line)+'\n'


def relation_proof(relation,names):
    name=relation['name']; states=['s'] if name=='initial' else ['s','t']
    args=' '.join(states); binders='('+' '.join(states)+' : State)'
    healthy=' '.join(f'(h{x} : regular {x})' for x in states)
    return '\n'.join(['import Translation','set_option veil.smt.trust false',
        'open RMVerify RMVerify.Reactive RMVerify.TypedSource Verified','set_option maxHeartbeats 8000000',
        f'theorem relation {binders} {healthy} : composed.{name} {args} ↔ specified_{name} {args} := by',
        indent(typed.tactic(names,contextual=False),'  '),
        f'theorem source_relation {binders} {healthy} : sourceModule.{name} {args} ↔ source_specified_{name} {args} := by',
        f'  simpa only [source_module_eq, specified_{name}_agreement] using relation {args} '+ ' '.join('h'+x for x in states),
        '#print axioms relation','#print axioms source_relation',''])


def differential(spec,model):
    count=0
    for atom in model['atoms']:
        component=spec.components[atom['component']]; local=list(fields_of(component.target))
        for item in atom['initial']+atom['actions']:
            p=model['programs'][item['index']]
            domains=[probes(k) for k in p.inputs]
            for values in islice(product(*domains),128):
                obj=object.__new__(component.target)
                for n,v in zip(local,deepcopy(values)): setattr(obj,n,v)
                pyfault=None
                try:
                    result=p.function(obj,**item['arguments']) if p.initialize else p.function(obj,*deepcopy(values[len(local):]))
                except (KeyError,AttributeError) as error: pyfault='missingKey' if isinstance(error,KeyError) else 'missingValue'
                actual=[getattr(obj,n) for n in local]
                try:
                    got=execute(p,list(values)); sourcefault=None; got=got[:-1]
                except ExecutionFault as error: got=error.fields;sourcefault=error.reason
                if actual!=got or pyfault!=sourcefault: raise ValueError('component translation mismatch')
                count+=1
    return count


def run(model,index,values):
    try: return execute(model['programs'][index],values)[:-1]+[None]
    except ExecutionFault as e: return e.fields+[e.reason]


def state_key(state):
    return json.dumps(data(state),sort_keys=True)

def unique(states):
    return list({state_key(s):s for s in states}.values())


def initial_states(model):
    states=[[default_value(k) for k in model['fields'].values()]+[None]*len(model['atoms'])]
    for atom in model['atoms']:
        updated=[]
        for s,a in product(states,atom['initial']):
            t=deepcopy(s)
            for n,v in zip(atom['controls']+[len(model['fields'])+atom['component']],run(model,a['index'],[])):t[n]=v
            updated.append(t)
        states=unique(updated)
    return states


def successors(model,state):
    candidates=[deepcopy(state)]
    for atom in model['atoms']:
        updated=[]; fault=len(model['fields'])+atom['component']
        for candidate in candidates:
            if atom['stutter'] or state[fault] is not None: updated.append(candidate)
            if state[fault] is not None: continue
            for action in atom['actions']:
                domains=[list(execute(model['programs'][p['domain']],state[:len(model['fields'])])[0]) if 'domain' in p else p['choices'] if 'choices' in p else list(state[p['variable']]) if p.get('choice') else [(candidate if p['awaited'] else state)[p['variable']]] for p in action['ports']]
                for args in product(*domains):
                    result=run(model,action['index'],[state[n] for n in atom['controls']]+list(args))
                    t=deepcopy(candidate)
                    for n,v in zip(atom['controls']+[fault],result): t[n]=v
                    updated.append(t)
        candidates=unique(updated)
    return candidates


def counterexamples(model,depth,timeout,unresolved):
    import time
    deadline=time.monotonic()+timeout
    initial=initial_states(model)
    paths=[[s] for s in initial]; seen=set(); found={}
    sampled=[list(s)+[None]*len(model['atoms']) for s in islice(product(*(probes(k) for k in model['fields'].values())),128)]
    for _ in range(depth+1):
        next_paths=[]
        for path in paths:
            state=path[-1]; key=state_key(state)
            if key in seen: continue
            seen.add(key)
            if 'no-fault' in unresolved and 'no-fault' not in found:
                for i,reason in enumerate(state[len(model['fields']):]):
                    if reason is not None:
                        found['no-fault']=dict(kind='reachable_fault',fault=reason,atom=i,states=path)
                        break
            for j,p in enumerate(model['invariants']):
                if p['identifier'] not in unresolved or p['identifier'] in found:continue
                try: holds=execute(model['programs'][p['index']],state[:len(model['fields'])])[0]
                except ExecutionFault: holds=False
                if not holds: found[p['identifier']]=dict(kind='reachable_invariant',invariant=j,states=path)
            if time.monotonic()>deadline:return found
            following=successors(model,state)
            if all(v is None for v in state[len(model['fields']):]):
                for r in model['relations']:
                    identifier=r['identifier']
                    if identifier not in unresolved or identifier in found:continue
                    candidates=[state] if r['name']=='initial' else unique(following+sampled)
                    for candidate in candidates:
                        if any(v is not None for v in candidate[len(model['fields']):]):continue
                        values=state[:len(model['fields'])]+(candidate[:len(model['fields'])] if r['name']=='step' else [])
                        try:specified=execute(model['programs'][r['index']],values)[0]
                        except ExecutionFault:specified=False
                        actual=any(state_key(state)==state_key(x) for x in initial) if r['name']=='initial' else any(state_key(candidate)==state_key(x) for x in following)
                        if specified!=actual:
                            found[identifier]=dict(kind='relation_mismatch',relation=r['name'],states=[state] if r['name']=='initial' else [state,candidate])
                            break
            if set(unresolved)<=set(found):return found
            next_paths.extend(path+[t] for t in following)
        paths=next_paths
    return found


def witness_proof(witness,names,model):
    from .composition import witness_proof as scalar
    # Concrete collection states retain dictionary insertion order. Set order
    # is immaterial under the per-program totality/permutation certificates.
    proposal=dict(witness,states=[[0]*len(s) for s in witness['states']])
    if witness['kind']=='reachable_fault':proposal.update(kind='reachable_invariant',invariant=0)
    proof=scalar(proposal,names).replace('open RMVerify RMVerify.Reactive Verified','open RMVerify RMVerify.TypedSource RMVerify.Reactive Verified')
    if witness['kind']=='relation_mismatch':
        relation=witness['relation']; states=['s'] if relation=='initial' else ['s','t']
        binders='('+' '.join(states)+' : State)'
        proof=proof.replace('∀ '+binders+',','∀ '+binders+' '+' '.join(f'(h{s} : regular {s})' for s in states)+',')
        args=' '.join(f'state{i}' for i in range(len(states)))
        proof=proof.replace('h '+args+')','h '+args+' '+ ' '.join(f'(by simp [regular, state{i}])' for i in range(len(states)))+')')
    kinds=list(model['fields'].values())
    for i,state in enumerate(witness['states']):
        values=[typed.value(v,k) for v,k in zip(state,kinds)]+['none' if v is None else f'some .{v}' for v in state[len(kinds):]]
        proof=re.sub(rf'def state{i} : State := .*',f'def state{i} : State := ⟨'+', '.join(values)+'⟩',proof)
    if witness['kind']=='reachable_fault':
        fault=witness['atom']; last=len(witness['states'])-1
        proof=proof.replace(f'inv0 state{last}',f'(state{last}.«$fault{fault}» = none)').replace('inv0 s',f'(s.«$fault{fault}» = none)').replace('sourceInv0 s',f'(s.«$fault{fault}» = none)')
    states=[f'state{i}' for i in range(len(witness['states']))]
    concrete = ('try simp only [composed, Reactive.Module.initial, Reactive.Module.step, List.forall_mem_cons]\n'
        'try dsimp only ['+', '.join([f'atom{i}' for i in range(len(model['atoms']))]+states)+']\n'
        'all_goals try simp\nall_goals first | decide | (\n'+indent(typed.tactic(names+states+['dictGet','dictSet','setAdd','setDiscard','allM','anyM','eachM']),'  ')+')')
    return proof.replace(indent(lean.tactic(names+states),'  '),indent(concrete,'  '))


def observer_definitions(model):
    ghosts=[(i,a) for i,a in enumerate(model['atoms']) if a.get('ghost')]
    if not ghosts:return [],[]
    ai,ghost=ghosts[0]
    fields=list(model['fields']); kinds=list(model['fields'].values())
    allfields=fields+[f'$fault{i}' for i in range(len(model['atoms']))]
    allkinds=[typed.kind(k) for k in kinds]+['Option Fault']*len(model['atoms'])
    gc=ghost['controls']+[len(fields)+ghost['component']]
    ec=[i for i in range(len(allfields)) if i not in gc]
    lines=['structure ExecutableState where']+[f'  «{allfields[i]}» : {allkinds[i]}' for i in ec]+['  deriving Repr, DecidableEq','structure GhostState where']+[f'  «{allfields[i]}» : {allkinds[i]}' for i in gc]+['  deriving Repr, DecidableEq']
    def make(indices,state):return '{'+', '.join(f'«{allfields[i]}» := {state}.«{allfields[i]}»' for i in indices)+'}'
    lines += [f'def erase (s : State) : ExecutableState := {make(ec,"s")}', f'def history (s : State) : GhostState := {make(gc,"s")}',
              'def embed (e : ExecutableState) (g : GhostState) : State := {'+', '.join(f'«{n}» := {"g" if i in gc else "e"}.«{n}»' for i,n in enumerate(allfields))+'}',
              'def emptyGhost : GhostState := {'+', '.join(f'«{allfields[i]}» := {typed.default(kinds[i]) if i<len(fields) else "none"}' for i in gc)+'}',
              '@[simp] theorem erase_embed (e : ExecutableState) (g : GhostState) : erase (embed e g) = e := rfl',
              '@[simp] theorem history_embed (e : ExecutableState) (g : GhostState) : history (embed e g) = g := rfl',
              '@[simp] theorem embed_projections (s : State) : embed (erase s) (history s) = s := rfl']
    execnames=[]
    for i,a in enumerate(model['atoms']):
        if a.get('ghost'):continue
        ctrl=a['controls']+[len(fields)+a['component']]
        lines += [f'def executableAtom{i} : Atom ExecutableState where',
                  f'  controls := {[ec.index(n) for n in ctrl]}',f'  reads := {[ec.index(n) for n in a["reads"]]}',f'  awaits := {[ec.index(n) for n in a["awaits"]]}',
                  f'  initial e := atom{i}.initial (embed e emptyGhost)',f'  step e e\' := atom{i}.step (embed e emptyGhost) (embed e\' emptyGhost)']
        execnames += [f'executableAtom{i}']
    lines += ['def executable : Reactive.Module ExecutableState := ⟨['+', '.join(execnames)+']⟩',
              f'theorem executable_well_formed : executable.wellFormed {len(ec)} = true := by decide','#print axioms executable_well_formed']
    init=ghost['initial'][0]['index']; action=ghost['actions'][0]; index=action['index']; p=model['programs'][index]
    values=[f's.«{fields[n]}»' for n in ghost['controls']]+[f'{"t" if port["awaited"] else "s"}.«{fields[port["variable"]]}»' for port in action['ports']]
    output=f'output{index} (compiled{index} ({typed.frame_value(p,values)}))'
    lines += [f'def ghostOutput (s t : State) := if s.«$fault{ghost["component"]}».isSome then {tuple_(projection(model,ghost,"s"))} else {output}']
    def ghost_value(value):
        return '{'+', '.join(f'«{allfields[n]}» := ({value})'+'.2'*j+('.1' if j<len(gc)-1 else '') for j,n in enumerate(gc))+'}'
    lines += [f'def initialGhost (_ : ExecutableState) : GhostState := {ghost_value(f"initialOutput{ai}")}',
              f'def observe (e : ExecutableState) (g : GhostState) (e\' : ExecutableState) : GhostState := {ghost_value("ghostOutput (embed e g) (embed e' emptyGhost)")}',
              'def decorated := observed executable initialGhost observe']
    reductions=['composed','executable','decorated','observed','Module.initial','Module.step',*execnames,*[f'atom{i}' for i in range(len(model['atoms']))],'embed','erase','history','initialGhost',f'initialOutput{ai}','observe','ghostOutput','GhostState.mk.injEq']
    simp='simp (config := {failIfUnchanged := false}) ['+', '.join(reductions)+', List.mem_cons, List.mem_singleton, forall_eq, Prod.mk.injEq]'
    # The executable clauses are identical; only the deterministic observer
    # equality is regrouped into a named ghost state.
    lines += ['theorem initial_observer (e : ExecutableState) (g : GhostState) : composed.initial (embed e g) ↔ decorated.initial (e,g) := by',
              '  cases g',indent(simp,'  '),'  all_goals grind',
              'theorem round_observer (e e\' : ExecutableState) (g g\' : GhostState) : composed.step (embed e g) (embed e\' g\') ↔ decorated.step (e,g) (e\',g\') := by',
              f'  by_cases hf : g.«$fault{ghost["component"]}».isSome = true <;> cases g <;> cases g\'', '  all_goals', indent(simp+' at *','    '), '  all_goals grind',
              'theorem observer_correspondence (s : State) : Reactive.Reachable composed s ↔ Reactive.Reachable decorated (erase s, history s) := by',
              '  constructor',
              '  · intro h; induction h with',
              '    | initial h => exact .initial ((initial_observer _ _).mp (by simpa using h))',
              '    | step _ h ih => exact .step ih ((round_observer _ _ _ _).mp (by simpa using h))',
              '  · generalize he : (erase s, history s) = pair',
              '    intro h; induction h generalizing s with',
              '    | initial h =>',
              '      cases he; exact .initial (by simpa using (initial_observer _ _).mpr h)',
              '    | @step pair next _ h ih =>',
              '      cases he',
              '      have prior := ih (embed pair.1 pair.2) (by simp)',
              '      exact .step prior (by simpa using (round_observer _ _ _ _).mpr h)',
              'theorem ghost_projection (s : State) (h : Reactive.Reachable composed s) : Reactive.Reachable executable (erase s) :=',
              '  observed_projects executable initialGhost observe _ ((observer_correspondence s).mp h)',
              'theorem ghost_extension (e : ExecutableState) (h : Reactive.Reachable executable e) : ∃ g, Reactive.Reachable composed (embed e g) := by',
              '  obtain ⟨g,hg⟩ := observed_extends executable initialGhost observe e h',
              '  exact ⟨g, (observer_correspondence (embed e g)).mpr (by simpa only [decorated, erase_embed, history_embed] using hg)⟩']
    audits=['executable_well_formed','initial_observer','round_observer','observer_correspondence','ghost_projection','ghost_extension']
    lines += [f'#print axioms {n}' for n in audits if n!='executable_well_formed']
    return lines,audits


def no_fault_proof(model,names):
    healthy=' ∧ '.join([f's.«$fault{i}» = none' for i in range(len(model['atoms']))]+['True'])
    source=invariant_proof(model,[n for n in names if n!='safe' and not re.fullmatch(r'inv\d+',n)]+['healthy'])
    source=source.replace('theorem invariant :',f'def healthy (s : State) : Prop := {healthy}\ntheorem healthy_agreement (s : State) : healthy s ↔ healthy s := Iff.rfl\ntheorem invariant :',1)
    source=re.sub(r'\bsafe\b','healthy',source).replace('sourceSafe','healthy').replace('safe_agreement','healthy_agreement')
    return source
