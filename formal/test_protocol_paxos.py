"""Saved original-coroutine/direct-RM compatibility checks. No algorithm repairs."""
from collections import Counter
from contextlib import redirect_stdout
import copy
import io
from pathlib import Path
import random
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from paxos_lab.algorithm import PaxosNode
from paxos_lab.transport import Message
from protocol_paxos import build, node_schema, node_update, VALUES, KINDS
from zrth.protocol import Field, ProtocolModule, Simulation, named_module


class Request:
    def __init__(self,method,args,kwargs): self.method,self.args,self.kwargs=method,args,kwargs
    def __await__(self): return (yield self)


class Port:
    node_id="n1"
    peers=("n1","n2","n3")
    async def send(self,*args,**kwargs): return await Request("send",args,kwargs)
    async def broadcast(self,*args,**kwargs): return await Request("broadcast",args,kwargs)


def advance(task,reply=None):
    with redirect_stdout(io.StringIO()):
        try: return task.send(reply)
        except StopIteration: return "done"
        except (KeyError,IndexError) as error: return type(error).__name__


def decode(s,limit):
    return dict(num=s["num"],promised_n=s["promised"],accepted_n=None if s["accepted_n"]==-1 else s["accepted_n"],
        accepted_value=VALUES[s["accepted"]],value=VALUES[s["own"]],
        proposed_value={n:VALUES[s[f"pv_{n}"]] for n in range(limit+1) if s[f"pv_has_{n}"]},
        promisers={n:{f"n{p+1}" for p in range(3) if s[f"prom_{n}_{p}"]} for n in range(limit+1) if s[f"prom_has_{n}"]},
        acceptors={n:{f"n{p+1}" for p in range(3) if s[f"acc_{n}_{p}"]} for n in range(limit+1) if s[f"acc_has_{n}"]},
        candidate_accepted={n:Counter({VALUES[v]:s[f"cand_{n}_count_{v}"] for v in sorted(range(1,len(VALUES)),key=lambda v:s[f"cand_{n}_rank_{v}"])
            if s[f"cand_{n}_count_{v}"]}) for n in range(limit+1) if s[f"cand_has_{n}"]})


@pytest.fixture(scope="module")
def node_artifact():
    state=node_schema(31)
    inputs={k:Field() for k in ("event","sender","number","value","prior_n","prior_v")}
    module,wires=named_module(state,inputs,lambda s,i:node_update(s,tuple(i.values()),31,31))
    return ProtocolModule("test-node","1",module,wires,state,inputs,()).artifact()


def call(original,simulation,method,args,encoded):
    task=getattr(original,method)(*args)
    try:
        expected=advance(task)
        simulation.step(**dict(zip(simulation.artifact["inputs"],encoded)))
        for _ in range(3):
            state=simulation.state
            assert state["status"]!=2
            assert decode(state,31)=={k:getattr(original,k) for k in decode(state,31)}
            for n,c in original.candidate_accepted.items():
                assert list(decode(state,31)["candidate_accepted"][n].items())==list(c.items())
            if isinstance(expected,Request):
                kind=next(k for k,v in KINDS.items() if v==state["out_kind"])
                payload={"num":state["out_num"]}
                if kind in ("accept","accepted"): payload["value"]=VALUES[state["out_value"]]
                if kind=="promise": payload["value"]={"num":state["out_num"],"accepted_n":None if state["out_prior_n"]==-1 else state["out_prior_n"],"accepted_value":VALUES[state["out_prior_v"]]}
                if expected.method=="broadcast":
                    assert state["out_target"]==-1 and expected.args==(kind,payload)
                    assert expected.kwargs=={"include_self":True}
                else: assert expected.args==(f"n{state['out_target']+1}",kind,payload)
                expected=advance(task,{} if expected.method=="broadcast" else None)
                simulation.step(event=3,sender=0,number=0,value=0,prior_n=-1,prior_v=0)
            else:
                assert (state["status"],state["fault"]) == ({"done":(0,0),"KeyError":(1,1),"IndexError":(1,2)}[expected])
                return
        raise AssertionError("unexpected suspension count")
    finally: task.close()


def test_original_coroutines(node_artifact):
    rng=random.Random(901)
    for case in range(35):
        original=PaxosNode(Port()); simulation=Simulation(node_artifact)
        call(original,simulation,"propose",(VALUES[1+case%5],),(1,0,0,1+case%5,-1,0))
        for _ in range(15):
            kind=rng.choice(list(KINDS)); n=rng.randrange(1,5); sender=rng.randrange(3); v=rng.randrange(6)
            payload={"num":n,"value":VALUES[v]}
            if kind=="promise": payload["value"]={"accepted_n":1,"accepted_value":VALUES[v]}
            call(original,simulation,"on_message",(Message(f"n{sender+1}",kind,payload),),
                 (KINDS[kind],sender,n,v,1,v if kind=="promise" else 0))
            if simulation.state["status"]: break


def test_tick_retry_boundary(node_artifact):
    original=PaxosNode(Port()); original.num=20; original.value="A"
    simulation=Simulation(node_artifact); simulation.state.update(num=20,own=1)
    call(original,simulation,"on_tick",(),(2,0,0,0,-1,0))
    assert original.num==22


@pytest.mark.parametrize("case",["empty","collision","tie"])
def test_counter_edge_cases(node_artifact,case):
    original=PaxosNode(Port()); original.value="A"
    sim=Simulation(node_artifact); sim.state.update(own=1,cand_has_1=1)
    original.candidate_accepted[1]=Counter()
    number,prior=1,0
    if case=="collision":
        original.candidate_accepted[1][1]=1
        sim.state.update(cand_1_count_4=1,cand_1_rank_4=0,cand_1_next=1)
        number,prior=2,4
    else:
        original.promisers[1]={"n1"}; sim.state.update(prom_has_1=1,prom_1_0=1)
        if case=="tie":
            original.candidate_accepted[1].update({"B":2,"A":2})
            sim.state.update(cand_1_count_2=2,cand_1_rank_2=0,cand_1_count_1=2,cand_1_rank_1=1,cand_1_next=2)
    message=Message("n2","promise",{"num":number,"value":{"accepted_n":1,"accepted_value":VALUES[prior]}})
    call(original,sim,"on_message",(message,),(11,1,number,0,1,prior))
    if case=="empty": assert sim.state["fault"]==2
    elif case=="collision": assert sim.state["fault"]==1
    else: assert original.proposed_value[1]=="B"


@pytest.fixture(scope="module")
def network(): return build().artifact()


def test_broadcast_fifo_and_resume(network):
    sim=Simulation(network)
    def act(action,node=0,value=0,slot=0): return sim.step(action=action,node=node,value=value,slot=slot)
    act(1,value=1)
    assert sim.state["n0_pc"]==2
    act(3)
    assert sim.state["invalid"]==1 and sim.state["n0_num"]==0
    for slot in (2,0,1): act(4,slot=slot)
    act(3)
    assert sim.state["n0_pc"]==0 and sim.state["n0_num"]==1
    act(5,node=1)
    assert sim.state["n1_promised"]==1
    assert sim.state["n1_pc"]==1
    assert any(sim.state[f"q{j}_kind"]==11 and sim.state[f"q{j}_phase"]==1 for j in range(6))


def test_overflow_is_explicit(network):
    sim=Simulation(network)
    for _ in range(4): sim.step(action=2,node=0,value=0,slot=0)
    assert sim.state["out_of_scope"]==1 and sim.state["n0_status"]==2
    before=dict(sim.state); sim.step(action=1,node=1,value=1,slot=0)
    assert sim.state==before


def test_capacity_is_explicit(network):
    sim=Simulation(network)
    for node in range(3): sim.step(action=1,node=node,value=1,slot=0)
    assert sim.state["out_of_scope"]==1


def test_network_against_original_coroutines(network):
    # The oracle runs algorithm.py itself, not another hand-written Paxos model.
    def packet(s,j):
        kind=next(k for k,v in KINDS.items() if v==s[f"q{j}_kind"])
        payload={"num":s[f"q{j}_num"]}
        if kind in ("accept","accepted"): payload["value"]=VALUES[s[f"q{j}_value"]]
        if kind=="promise":
            payload["value"]={"num":s[f"q{j}_num"],
                "accepted_n":None if s[f"q{j}_prior_n"]==-1 else s[f"q{j}_prior_n"],
                "accepted_value":VALUES[s[f"q{j}_prior_v"]]}
        return (s[f"q{j}_sender"],s[f"q{j}_target"],kind,payload)

    for seed in range(8):
        rng=random.Random(seed); sim=Simulation(network)
        ports=[Port() for _ in range(3)]
        for n,port in enumerate(ports): port.node_id=f"n{n+1}"
        nodes=[PaxosNode(port) for port in ports]
        tasks=[None]*3; suspended=[None]*3; failed=[None]*3
        pending=[]; inboxes=[[] for _ in nodes]
        def advance_node(n,reply=None):
            result=advance(tasks[n],reply)
            suspended[n]=result if isinstance(result,Request) else None
            if isinstance(result,Request):
                if result.method=="broadcast":
                    assert result.kwargs=={"include_self":True}
                    kind,payload=result.args
                    pending.extend((n,r,kind,copy.deepcopy(payload)) for r in range(3))
                else:
                    recipient,kind,payload=result.args
                    pending.append((n,int(recipient[1:])-1,kind,copy.deepcopy(payload)))
            elif result!="done": failed[n]=result
        try:
            for t in range(90):
                options=[("idle",)]
                for n in range(3):
                    if failed[n]: continue
                    if suspended[n]:
                        if not any(p[0]==n for p in pending): options.append(("resume",n))
                    else:
                        if inboxes[n]: options.append(("receive",n))
                        if t<8: options.append(("propose",n,1+n%2))
                options.extend(("deliver",j) for j in range(len(pending)))
                action=rng.choice(options); inp=dict(action=0,node=0,value=0,slot=0)
                if action[0]=="deliver":
                    p=pending.pop(action[1])
                    matches=[j for j in range(6) if sim.state[f"q{j}_phase"]==1 and packet(sim.state,j)==p]
                    assert matches
                    inp.update(action=4,slot=matches[0]); inboxes[p[1]].append(p)
                elif action[0]!="idle":
                    n=action[1]
                    inp.update(action={"propose":1,"resume":3,"receive":5}[action[0]],node=n)
                    if action[0]=="resume":
                        advance_node(n,{} if suspended[n].method=="broadcast" else None)
                    else:
                        if action[0]=="propose":
                            inp["value"]=action[2]; tasks[n]=nodes[n].propose(VALUES[action[2]])
                        else:
                            sender,_,kind,payload=inboxes[n].pop(0)
                            tasks[n]=nodes[n].on_message(Message(f"n{sender+1}",kind,payload))
                        advance_node(n)
                sim.step(**inp)
                if sim.state["out_of_scope"]: break
                assert sim.state["invalid"]==0
                for n,node in enumerate(nodes):
                    local={k:sim.state[f"n{n}_{k}"] for k in node_schema(3)}
                    decoded=decode(local,3)
                    assert decoded=={k:getattr(node,k) for k in decoded},(seed,t,action,n)
                    assert bool(local["pc"])==bool(suspended[n])
                    assert local["fault"]=={None:0,"KeyError":1,"IndexError":2}[failed[n]]
                    actual=sorted((sim.state[f"q{j}_order"],j) for j in range(6)
                        if sim.state[f"q{j}_phase"]==2 and sim.state[f"q{j}_target"]==n)
                    assert [rank for rank,_ in actual]==list(range(len(inboxes[n])))
                    assert [packet(sim.state,j) for _,j in actual]==inboxes[n]
                actual=[packet(sim.state,j) for j in range(6) if sim.state[f"q{j}_phase"]==1]
                assert sorted(map(repr,actual))==sorted(map(repr,pending))
        finally:
            for task in tasks:
                if task is not None: task.close()
