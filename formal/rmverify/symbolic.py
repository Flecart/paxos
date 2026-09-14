"""Veil diagnostic queries. Only separately replayed witnesses refute claims."""
import json
from . import lean_backend as lean
from . import typed_backend
from .recheck import solver_plugins


def search(directory, model, names, *, composition, typed, depth, timeout):
    relation='composed' if composition else 'model.toModule'
    reductions=names+['Reactive.Module.toVeil','Veil.RelationalTransitionSystem.next',
                     'RMVerify.Model.toModule','Reactive.Module.initial','Reactive.Module.step']
    if typed:reductions += typed_backend.REDUCE.split(', ')
    else:reductions += lean.UNFOLD.split(', ')
    reports=[]
    for name,kind,bound in [('VeilInduction','counterexample_to_induction',1),
                            ('VeilTrace','bounded_symbolic_trace',depth)]:
        states=[f's{i}' for i in range(bound+1)]
        hypotheses=[f'(start : {"safe s0" if kind=="counterexample_to_induction" else relation+".toVeil.init () s0"})']
        hypotheses += [f'(round{i} : {relation}.toVeil.next () s{i} s{i+1})' for i in range(bound)]
        source='\n'.join(['import Veil','import Translation','set_option veil.smt.trust false',
                         'set_option veil.smt.timeout 5','set_option maxHeartbeats 500000','set_option linter.all false',
                         'open RMVerify RMVerify.Reactive RMVerify.TypedSource Verified' if typed else 'open RMVerify RMVerify.Reactive Verified',
                         'example ('+' '.join(states)+' : State) '+' '.join(hypotheses)+f' : safe s{bound} := by',
                         '  '+'; '.join(f'cases {s}' for s in states),
                         '  simp (config := {maxSteps := 20000, failIfUnchanged := false}) ['+', '.join(reductions)+'] at *',
                         '  all_goals veil_bmc',''])
        (directory/f'{name}.lean').write_text(source)
        log=directory/f'{name}.log'
        code=lean.command(directory,['lean','-j1',*solver_plugins(directory,source),f'{name}.lean'],log,min(timeout,15))
        text=log.read_text()
        status='candidate' if 'potential counter-example:' in text else 'no-candidate' if code==0 else 'unknown'
        result=dict(kind=kind,status=status,checked_witness=False,log=log.name)
        if kind=='bounded_symbolic_trace':result['round_bound']=bound
        (directory/f'{name}.json').write_text(json.dumps(result,indent=2)+'\n')
        reports.append(result)
    return reports
