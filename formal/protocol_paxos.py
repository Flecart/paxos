"""Bug-preserving, manually authored RM protocol. Not a source translator.

All mutable node/network/monitor state lives in ordinary RM wires. Python loops
below only construct a finite symbolic circuit; they never execute a protocol.
"""
from pathlib import Path
from zrth.protocol import (Field, ProtocolModule, PropertySpec, named_module,
                           ref, lit, op, conjunction, disjunction, implies)
from zrth.protocol_layout import (FiniteMap, MembershipSet, OrderedCounter,
                                  select, any_of, all_of, ite)

VALUES = (None, "A", "B", 0, 1, 2)
KINDS = {"propose":10,"promise":11,"accept":12,"accepted":13,"reject":14}
ROOT = Path(__file__).resolve().parent


def node_schema(limit):
    state={k:Field(v) for k,v in dict(num=0,promised=-1,accepted_n=-1,accepted=0,
        own=0,pc=0,status=0,fault=0,out_kind=0,out_target=0,out_num=0,out_value=0,
        out_prior_n=-1,out_prior_v=0,declared=0,declared_num=0,declared_value=0).items()}
    state.update(FiniteMap("pv",range(limit+1)).schema())
    for n in range(limit+1):
        state.update({f"{k}_has_{n}":Field() for k in ("prom","acc","cand")})
        state.update(MembershipSet(f"prom_{n}",range(3)).schema())
        state.update(MembershipSet(f"acc_{n}",range(3)).schema())
        state.update(OrderedCounter(f"cand_{n}",range(1,len(VALUES))).schema())
    return state


def node_update(original, incoming, limit, max_count):
    s=dict(original)
    event,sender,number,value,prior_n,prior_v=incoming
    def put(k,v,g): s[k]=ite(g,v,s[k])
    def error(code,g): put("status",1,g); put("fault",code,g)
    def send(kind,target,num,g,value=0,prior_n=-1,prior_v=0,pc=1):
        for k,v in dict(out_kind=KINDS[kind],out_target=target,out_num=num,
                        out_value=value,out_prior_n=prior_n,out_prior_v=prior_v,pc=pc).items(): put(k,v,g)
    s["out_kind"],s["declared"]=0,0
    running=original["status"]==0
    idle=running & (original["pc"]==0)
    resume=running & (original["pc"]!=0) & (event==3)
    put("num",s["num"]+ite(original["pc"]==2,1,ite(original["pc"]==3,2,0)),resume)
    put("pc",0,resume)
    tick=idle & (event==2)
    proposal=idle & ((event==1)|((event==2)&(original["num"]>=20)&(original["accepted"]==0)))
    offered=ite(event==1,value,original["own"])
    valid=proposal & (offered!=0) & ((original["own"]==0)|(original["own"]==offered))
    put("own",offered,valid)
    send("propose",-1,original["num"]+1,valid,pc=ite(event==2,3,2))
    put("num",s["num"]+1,tick & ~valid)
    message=idle & (event>=10)&(event<=14)
    stale=message & (number<original["num"])
    send("reject",sender,original["num"],stale)
    current=message & ~stale
    prepare=current & (event==10)
    fresh=prepare & (number>original["promised"])
    put("num",ite(number>s["num"],number,s["num"]),prepare | (current & ((event==14)|(event==12)|(event==13))))
    put("promised",number,fresh)
    send("promise",sender,number,fresh,prior_n=s["accepted_n"],prior_v=s["accepted"])
    send("reject",sender,s["num"],prepare & ~fresh)
    accept=current & (event==12)
    accepts=accept & ((original["accepted"]==0)|(original["accepted"]==value))
    FiniteMap("pv",range(limit+1)).put(s,number,value,accepts)
    put("accepted",value,accepts); put("accepted_n",number,accepts)
    send("accepted",sender,number,accepts,value=value)
    send("reject",sender,s["num"],accept & ~accepts)
    promise=current & (event==11)
    # The original tests accepted VALUE membership in a NUMBER-keyed dictionary.
    present=ite(prior_v==-1,1,0)
    for code,raw in enumerate(VALUES):
        if type(raw) is int and 0<=raw<=limit:
            present=ite(prior_v==code,s[f"cand_has_{raw}"],present)
    for n in range(limit+1):
        g=promise & (number==n)
        counter=OrderedCounter(f"cand_{n}",range(1,len(VALUES)))
        increment=g & (prior_v!=0)
        reset=increment & (present==0)
        put(f"cand_has_{n}",1,reset)
        for name in counter.schema(): put(name,0,reset)
        missing=increment & (s[f"cand_has_{n}"]==0)
        error(1,missing)
        counter.increment(s,prior_v,increment & ~missing)
        good=g & (s["status"]==0)
        put(f"prom_has_{n}",1,good)
        members=MembershipSet(f"prom_{n}",range(3)); members.add(s,sender,good)
        majority=good & (members.size(s)>1)
        candidates=any_of(s[f"cand_has_{i}"]!=0 for i in range(limit+1))
        error(1,majority & candidates & (s[f"cand_has_{n}"]==0))
        choice,count=counter.most_common(s,s["own"])
        error(2,majority & candidates & (s[f"cand_has_{n}"]!=0) & (count==0))
        choice=ite(candidates,choice,s["own"])
        sendable=majority & (s["status"]==0)
        put(f"pv_has_{n}",1,sendable); put(f"pv_{n}",choice,sendable)
        send("accept",-1,number,sendable,value=choice)
    accepted=current & (event==13)
    for n in range(limit+1):
        g=accepted & (number==n)
        put(f"acc_has_{n}",1,g)
        members=MembershipSet(f"acc_{n}",range(3)); members.add(s,sender,g)
        declares=g & (members.size(s)>1) & (s["accepted"]==0)
        missing=declares & (s[f"pv_has_{n}"]==0)
        error(1,missing)
        declares=declares & ~missing
        for k,v in dict(declared=1,declared_num=number,declared_value=s[f"pv_{n}"],accepted=value).items(): put(k,v,declares)
    overflow=(s["num"]>limit)|(s["out_num"]>limit)|(number>limit)
    overflow=overflow | any_of(s[f"cand_{n}_count_{v}"]>max_count for n in range(limit+1) for v in range(1,len(VALUES)))
    put("status",2,overflow)
    return s


def build(profile="small"):
    if profile not in ("small","compatibility"): raise ValueError("unknown profile")
    limit,capacity=(3,6) if profile=="small" else (31,32)
    local=node_schema(limit)
    state={f"n{n}_{k}":f for n in range(3) for k,f in local.items()}
    state.update({k:Field() for k in ("out_of_scope","invalid","bad_decision")})
    packet=("sender","target","kind","num","value","prior_n","prior_v")
    for slot in range(capacity):
        state.update({f"q{slot}_{k}":Field() for k in ("phase","order",*packet)})
    state.update({f"submitted_{v}":Field() for v in range(len(VALUES))})
    state.update({f"announced_{v}":Field() for v in range(len(VALUES))})
    state.update({f"vote_{n}_{r}_{v}":Field() for n in range(3) for r in range(limit+1) for v in range(len(VALUES))})
    inputs={"action":Field(minimum=0,maximum=5,labels={0:"idle",1:"propose",2:"tick",3:"resume",4:"deliver",5:"receive"}),
            "node":Field(minimum=0,maximum=2),"value":Field(minimum=0,maximum=5),
            "slot":Field(minimum=0,maximum=capacity-1)}

    def transition(s,i):
        before=dict(s); action,node,value,slot=(i[k] for k in inputs)
        active=s["out_of_scope"]==0
        def put(k,v,g): s[k]=ite(g,v,s[k])
        # Receive selects the unique FIFO head internally, independent of slot.
        head=-1
        for j in reversed(range(capacity)):
            head=ite((s[f"q{j}_phase"]==2)&(s[f"q{j}_target"]==node)&(s[f"q{j}_order"]==0),j,head)
        msg={k:select([s[f"q{j}_{k}"] for j in range(capacity)],head,0) for k in packet}
        outgoing=[]; legal=action==0
        for n in range(3):
            old={k:s[f"n{n}_{k}"] for k in local}
            pending=any_of((s[f"q{j}_phase"]==1)&(s[f"q{j}_sender"]==n) for j in range(capacity))
            ready=(old["status"]==0)&(old["pc"]==0)
            can=(node==n)&((ready&((action==1)|(action==2)|((action==5)&(head>=0))))|
                ((old["status"]==0)&(old["pc"]!=0)&~pending&(action==3)))
            legal=legal|can
            dispatch=active&can
            event=ite(action==5,msg["kind"],action)
            arguments=(event,ite(action==5,msg["sender"],0),ite(action==5,msg["num"],0),
                       ite(action==5,msg["value"],value),ite(action==5,msg["prior_n"],-1),ite(action==5,msg["prior_v"],0))
            nxt=node_update(old,arguments,limit,limit)
            for k in local: put(f"n{n}_{k}",nxt[k],dispatch)
            put("out_of_scope",1,dispatch&(nxt["status"]==2))
            for v in range(1,len(VALUES)): put(f"submitted_{v}",1,dispatch&(action==1)&(value==v))
            consume=dispatch&(action==5)
            for j in range(capacity):
                put(f"q{j}_phase",0,consume&(head==j))
                put(f"q{j}_order",s[f"q{j}_order"]-1,consume&(before[f"q{j}_phase"]==2)&(before[f"q{j}_target"]==n)&(before[f"q{j}_order"]>0))
            outgoing.append((n,nxt,dispatch))
        deliver=active&(action==4)&(select([before[f"q{j}_phase"] for j in range(capacity)],slot,0)==1)
        legal=legal|((action==4)&(select([before[f"q{j}_phase"] for j in range(capacity)],slot,0)==1))
        target=select([before[f"q{j}_target"] for j in range(capacity)],slot,0)
        length=sum(ite((before[f"q{j}_phase"]==2)&(before[f"q{j}_target"]==target),1,0) for j in range(capacity))
        for j in range(capacity):
            put(f"q{j}_phase",2,deliver&(slot==j)); put(f"q{j}_order",length,deliver&(slot==j))
        put("invalid",ite(legal,0,1),active)
        for n,nxt,dispatch in outgoing:
            emit=dispatch&(nxt["status"]==0)&(nxt["out_kind"]!=0)
            count=sum(ite(s[f"q{j}_phase"]!=0,1,0) for j in range(capacity))
            needed=ite(nxt["out_target"]==-1,3,1)
            overflow=emit&(count+needed>capacity)
            put("out_of_scope",1,overflow)
            for r in range(3):
                enabled=emit&~overflow&((nxt["out_target"]==-1)|(nxt["out_target"]==r))
                free=-1
                for j in reversed(range(capacity)): free=ite(s[f"q{j}_phase"]==0,j,free)
                data=dict(sender=n,target=r,kind=nxt["out_kind"],num=nxt["out_num"],
                          value=nxt["out_value"],prior_n=nxt["out_prior_n"],prior_v=nxt["out_prior_v"],order=0,phase=1)
                for j in range(capacity):
                    for k,v in data.items(): put(f"q{j}_{k}",v,enabled&(free==j))
            for r in range(limit+1):
                for v in range(len(VALUES)):
                    put(f"vote_{n}_{r}_{v}",1,emit&(nxt["out_kind"]==13)&(nxt["out_num"]==r)&(nxt["out_value"]==v))
            for v in range(len(VALUES)):
                declared=dispatch&(nxt["status"]==0)&(nxt["declared"]!=0)&(nxt["declared_value"]==v)
                put(f"announced_{v}",1,declared)
                chosen=any_of(sum(s[f"vote_{p}_{r}_{v}"] for p in range(3))>1 for r in range(limit+1))
                put("bad_decision",1,declared&~chosen)
        return s

    module,wires=named_module(state,inputs,transition)
    eq=lambda a,b:op("eq",a,b)
    def chosen(v):
        return disjunction(op("gt",op("add",op("add",ref(f"vote_0_{r}_{v}"),ref(f"vote_1_{r}_{v}")),ref(f"vote_2_{r}_{v}")),lit(1)) for r in range(limit+1))
    in_scope=eq(ref("out_of_scope"),lit(0))
    properties=[]
    def invariant(name,formula): properties.append(PropertySpec(name,implies(in_scope,formula)))
    invariant("agreement",conjunction(["not",op("and",chosen(a),chosen(b))] for a in range(len(VALUES)) for b in range(a+1,len(VALUES))))
    invariant("validity",conjunction(implies(chosen(v),eq(ref(f"submitted_{v}"),lit(1))) for v in range(len(VALUES))))
    invariant("decision_accuracy",eq(ref("bad_decision"),lit(0)))
    invariant("decision_consistency",conjunction(["not",op("and",eq(ref(f"announced_{a}"),lit(1)),eq(ref(f"announced_{b}"),lit(1)))] for a in range(len(VALUES)) for b in range(a+1,len(VALUES))))
    invariant("fault_freedom",conjunction(eq(ref(f"n{n}_status"),lit(0)) for n in range(3)))
    for n in range(3):
        valid_step=op("and",in_scope,eq(ref("out_of_scope","next"),lit(0)))
        stable=implies(op("ne",ref(f"n{n}_accepted"),lit(0)),eq(ref(f"n{n}_accepted","next"),ref(f"n{n}_accepted")))
        properties.append(PropertySpec(f"n{n}_non_none_acceptance_is_immutable",implies(valid_step,stable),"step"))
        reply=implies(eq(ref(f"n{n}_out_kind","next"),lit(13)),eq(ref(f"n{n}_out_value","next"),ref(f"n{n}_accepted","next")))
        properties.append(PropertySpec(f"n{n}_acceptance_reply_matches_recorded_value",implies(valid_step,reply),"step"))
    properties.append(PropertySpec("unconditional_proposal_liveness",disjunction(chosen(v) for v in range(len(VALUES))),"leads-to",
        trigger=op("and",in_scope,disjunction(eq(ref(f"submitted_{v}"),lit(1)) for v in range(1,len(VALUES)))),
        witness={"initial_inputs":[0,0,0,0],"actions":[[1,0,1,0]],"idle":[0,0,0,0]}))
    return ProtocolModule("paxos-learning","1",module,wires,state,inputs,
        tuple(f"n{n}_{k}" for n in range(3) for k in ("accepted","declared","declared_value")),tuple(properties),
        assumptions={"network":"reliable asynchronous delivery; no crashes, loss, duplication, forged messages or retries",
                     "scope":"safety claims are conditional on out_of_scope=0; invalid scheduler actions stutter",
                     "fairness":"none; idle is always enabled"},
        profile=dict(name=profile,nodes=3,values=VALUES,max_number=limit,max_count=limit,capacity=capacity,
                     source_equivalence="not-established; manual port requires separate differential checks"),
        sources=(str(__file__),str(ROOT.parent/"paxos_lab"/"algorithm.py")))
