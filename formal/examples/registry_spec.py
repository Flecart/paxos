"""Immutable messages by ID, shared reads and an exclusive local borrow."""
from dataclasses import dataclass
from rmverify import Specification,Contract,Call,Trace

@dataclass(frozen=True)
class Message:
    key:int
    payload:int

class Registry:
    entries:dict[int,Message]
    ids:set[int]
    def __init__(self)->None:
        self.entries={}
        self.ids=set()
    def register(self,key:int,payload:int)->Message:
        entries=self.entries
        if key not in entries:
            entries[key]=Message(key,payload)
            self.ids.add(key)
        return entries[key]

def domains(s:Registry)->bool:
    return len(s.entries)==len(s.ids) and all(key in s.ids for key in s.entries) and all(key in s.entries for key in s.ids)

def stored(before:Registry,after:Registry,result:Message,key:int,payload:int)->bool:
    return result==after.entries[key] and (result==before.entries[key] if key in before.entries else result==Message(key,payload)) and (len(after.entries)==len(before.entries) if key in before.entries else len(after.entries)==len(before.entries)+1)

spec=Specification(Registry,[Registry.register],[domains],{Registry.register:Contract(ensures=stored)},checks=[Trace([Call('register',key=3,payload=7),Call('register',key=3,payload=99)])])
