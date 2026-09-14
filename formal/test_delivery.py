"""Finite choice, complete-round delivery, and checked negative executions."""
from copy import deepcopy
from pathlib import Path
import unittest
from rmverify import Await,Choice,Component,Composition,verify
from rmverify.composition import prepare_model
from rmverify.typed_composition import initial_states,successors
from rmverify.frontend import Unsupported
from examples.delivery_spec import spec,broken

class Pool:
    ids:set[int]
    def __init__(self)->None:self.ids={1,2}
    def clear(self)->None:self.ids=set()
class Sink:
    key:int
    def __init__(self)->None:self.key=0
    def select(self,key:int)->None:self.key=key
class Pair:
    ids:set[int]
    key:int
def nonnegative(s:Pair)->bool:return s.key>=0
def positive_domain(s:Pair)->bool:return all(k>=0 for k in s.ids)
def available(s:Pair)->set[int]:return s.ids

def choices(domain):
    return Composition(Pair,[Component(Pool,[Pool.clear],{'ids':'ids'}),Component(Sink,[Sink.select],{'key':'key'},{'key':Choice(domain)})],[nonnegative],[positive_domain])

class DeliveryTests(unittest.TestCase):
    def test_finite_old_domains_and_empty_stuttering(self):
        for domain in ('ids',available,(1,2)):
            model=prepare_model(choices(domain))
            states=successors(model,initial_states(model)[0])
            self.assertTrue(any(s[0]==set() and s[1]==2 for s in states))
            if domain!=(1,2):self.assertEqual(successors(model,[set(),0,None,None]),[[set(),0,None,None]])
        report=verify(choices(available),timeout=120)
        self.assertTrue(report.ok,report)
        self.assertIn('domain_total',(Path(report.evidence)/'Translation.log').read_text())

    def test_ghost_cannot_control_executable_behavior(self):
        invalid=deepcopy(spec)
        invalid.components[1].inputs['selected']=Choice('sent')
        with self.assertRaisesRegex(Unsupported,'ghost'):prepare_model(invalid)

    def test_registry(self):
        from examples.registry_spec import spec as registry
        report=verify(registry,timeout=120)
        self.assertTrue(report.ok,report)

    def test_delivery_and_reachable_duplicate(self):
        report=verify(spec,timeout=180,depth=4)
        self.assertTrue(report.ok,report)
        audit=(Path(report.evidence)/'Translation.log').read_text()
        for name in ('ghost_projection','ghost_extension','composition_correspondence'):self.assertIn(name,audit)
        report=verify(broken,timeout=180,depth=4)
        self.assertEqual(report.status,'refuted',report)
        for name in ('consistent','at_most_once'):
            claim=report.properties['invariant:'+name]
            self.assertEqual(claim['status'],'refuted',report)
            self.assertEqual(claim['witness']['kind'],'reachable_invariant')
        self.assertEqual(report.properties['no-fault']['status'],'proved',report)


class Lookup:
    entries:dict[int,int]
    value:int
    def __init__(self)->None:
        self.entries={}
        self.value=0
    def read(self)->None:self.value=self.entries[0]
def unconstrained(s:Lookup)->bool:return True
faulty=Composition(Lookup,[Component(Lookup,[Lookup.read],{'entries':'entries','value':'value'})],[unconstrained])

class Keys:
    ids:set[int]
    def __init__(self)->None:self.ids=set()
    def add(self)->None:self.ids.add(1)
def bounded(s:Keys)->bool:return len(s.ids)<=1
def unchanged_size(s:Keys,t:Keys)->bool:return len(t.ids)==len(s.ids)
relation_mismatch=Composition(Keys,[Component(Keys,[Keys.add],{'ids':'ids'})],[bounded],step_relation=unchanged_size)

class FailureTests(unittest.TestCase):
    def test_fault_and_relation_replays(self):
        for spec_,key,kind in [(faulty,'no-fault','reachable_fault'),(relation_mismatch,'relation:unchanged_size','relation_mismatch')]:
            report=verify(spec_,timeout=90,depth=2)
            self.assertEqual(report.properties[key]['status'],'refuted',report)
            self.assertEqual(report.properties[key]['witness']['kind'],kind)


from rmverify import Specification,Contract
from examples.registry_spec import Registry,Message,domains

def wrong_payload(before:Registry,after:Registry,result:Message,key:int,payload:int)->bool:
    return result==Message(key,payload)

class ContractFailureTests(unittest.TestCase):
    def test_rich_contract_refutation(self):
        spec=Specification(Registry,[Registry.register],[domains],{Registry.register:Contract(ensures=wrong_payload)})
        report=verify(spec,timeout=120,depth=2)
        claim=report.properties['contract:Registry.register']
        self.assertEqual(claim['status'],'refuted',report)
        self.assertEqual(claim['witness']['kind'],'reachable_contract')

if __name__=='__main__':unittest.main()
