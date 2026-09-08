"""Lower the pinned learning implementation to ordinary, analyzer-supported Python.

This is a source-specific translation, not a general Python compiler. The hash
guard requires review after the original changes. Generated methods contain only
scalar assignments, comparisons, arithmetic, and conditional control flow.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text())
LIMIT = CONFIG["max_number"]
VALUES = CONFIG["values"]
INPUTS = ["event", "sender", "number", "value", "prior_number", "prior_value"]
# events: proposal=1, tick=2, resume=3; wire messages=10..14
KINDS = {"propose": 10, "promise": 11, "accept": 12, "accepted": 13, "reject": 14}


def state_schema():
    state = dict(num=0, promised=-1, accepted_n=-1, accepted=0, own=0,
                 pc=0, status=0, fault=0, out_kind=0, out_target=0,
                 out_num=0, out_value=0, out_prior_n=-1, out_prior_v=0,
                 declared=0, declared_num=0, declared_value=0)
    for n in range(LIMIT + 1):
        state.update({f"pv_has_{n}": 0, f"pv_{n}": 0,
                      f"prom_has_{n}": 0, f"acc_has_{n}": 0,
                      f"cand_has_{n}": 0, f"next_rank_{n}": 0})
        for p in range(3):
            state[f"prom_{n}_{p}"] = 0
            state[f"acc_{n}_{p}"] = 0
        for v in range(1, len(VALUES)):
            state[f"count_{n}_{v}"] = 0
            state[f"rank_{n}_{v}"] = 0
    return state


class Code:
    def __init__(self):
        self.lines = []

    def add(self, text, indent=0):
        self.lines.append("    " * indent + text)

    def assign(self, name, expression, indent):
        self.add(f"self.{name} = {expression}", indent)

    def error(self, code, indent):
        self.assign("status", "1", indent)
        self.assign("fault", str(code), indent)

    def send(self, kind, target, num, value="0", prior_n="-1", prior_v="0", pc=1, indent=0):
        for field, expr in (("out_kind", str(KINDS[kind])), ("out_target", target),
                            ("out_num", num), ("out_value", value),
                            ("out_prior_n", prior_n), ("out_prior_v", prior_v),
                            ("pc", str(pc))):
            self.assign(field, expr, indent)

    def proposal(self, val, tick, indent):
        self.add(f"if {val} != 0 and (self.own == 0 or self.own == {val}):", indent)
        self.assign("own", val, indent + 1)
        self.send("propose", "-1", "self.num + 1", pc=3 if tick else 2, indent=indent + 1)
        if tick:
            self.add("else:", indent)
            self.assign("num", "self.num + 1", indent + 1)


def generate():
    original = ROOT.parent / "paxos_lab" / "algorithm.py"
    actual = hashlib.sha256(original.read_bytes()).hexdigest()
    if actual != CONFIG["source_sha256"]:
        raise SystemExit("Original algorithm changed: review the source-specific lowering before updating its hash")
    schema = state_schema()
    c = Code()
    c.add('"""Generated executable Python. Source mapping and bounds: manifest.json. Do not edit."""')
    c.add("class Node:")
    c.add("def __init__(self):", 1)
    c.add("self.reset()", 2)
    c.add("def reset(self):", 1)
    for key, val in schema.items():
        c.assign(key, str(val), 2)
    c.add("return 0", 2)
    c.add("def step(self, " + ", ".join(INPUTS) + "):", 1)
    # Explicit holds keep the analyzer's output relation total.
    for key in schema:
        c.assign(key, f"self.{key}", 2)
    c.assign("out_kind", "0", 2)
    c.assign("declared", "0", 2)
    c.add("if self.status == 0:", 2)
    c.add("if self.pc != 0:", 3)
    c.add("if event == 3:", 4)
    c.add("if self.pc == 2:", 5)
    c.assign("num", "self.num + 1", 6)
    c.add("elif self.pc == 3:", 5)
    c.assign("num", "self.num + 2", 6)
    c.assign("pc", "0", 5)
    c.add("elif event == 1:", 3)
    c.proposal("value", False, 4)
    c.add("elif event == 2:", 3)
    # For reachable nonnegative num, bool(num // 20) == (num >= 20).
    c.add("if self.num >= 20 and self.accepted == 0:", 4)
    c.proposal("self.own", True, 5)
    c.add("else:", 4)
    c.assign("num", "self.num + 1", 5)
    c.add("elif event >= 10 and event <= 14:", 3)
    c.add("if number < self.num:", 4)
    c.send("reject", "sender", "self.num", indent=5)
    c.add("elif event == 10:", 4)
    c.assign("num", "max(self.num, number)", 5)
    c.add("if number > self.promised:", 5)
    c.assign("promised", "number", 6)
    c.send("promise", "sender", "self.promised", prior_n="self.accepted_n", prior_v="self.accepted", indent=6)
    c.add("else:", 5)
    c.send("reject", "sender", "self.num", indent=6)
    c.add("elif event == 14:", 4)
    c.assign("num", "max(self.num, number)", 5)
    c.add("elif event == 12:", 4)
    c.assign("num", "max(self.num, number)", 5)
    c.add("if self.accepted == 0 or self.accepted == value:", 5)
    for n in range(LIMIT + 1):
        c.add(f"if number == {n}:", 6)
        c.assign(f"pv_has_{n}", "1", 7)
        c.assign(f"pv_{n}", "value", 7)
    c.assign("accepted", "value", 6)
    c.assign("accepted_n", "number", 6)
    c.send("accepted", "sender", "number", "value", indent=6)
    c.add("else:", 5)
    c.send("reject", "sender", "self.num", indent=6)
    c.add("elif event == 11:", 4)
    # The source tests accepted VALUE membership in a dictionary keyed by NUMBER.
    # Preserve integer-key collisions (codes 3,4,5 mean Python ints 0,1,2).
    c.add("present = self.num - self.num", 5)
    for val_code, raw in enumerate(VALUES):
        if type(raw) is int and 0 <= raw <= LIMIT:
            c.add(f"if prior_value == {val_code}:", 5)
            c.add(f"present = self.cand_has_{raw}", 6)
    for n in range(LIMIT + 1):
        c.add(f"if number == {n}:", 5)
        c.add("if prior_value != 0:", 6)
        c.add("if present == 0:", 7)
        c.assign(f"cand_has_{n}", "1", 8)
        c.assign(f"next_rank_{n}", "0", 8)
        for v in range(1, len(VALUES)):
            c.assign(f"count_{n}_{v}", "0", 8)
            c.assign(f"rank_{n}_{v}", "0", 8)
        c.add(f"if self.cand_has_{n} == 0:", 7)
        c.error(1, 8)
        c.add("else:", 7)
        for v in range(1, len(VALUES)):
            c.add(f"if prior_value == {v}:", 8)
            c.add(f"if self.count_{n}_{v} == 0:", 9)
            c.assign(f"rank_{n}_{v}", f"self.next_rank_{n}", 10)
            c.assign(f"next_rank_{n}", f"self.next_rank_{n} + 1", 10)
            c.assign(f"count_{n}_{v}", f"self.count_{n}_{v} + 1", 9)
        c.add("if self.status == 0:", 6)
        c.assign(f"prom_has_{n}", "1", 7)
        for p in range(3):
            c.add(f"if sender == {p}:", 7)
            c.assign(f"prom_{n}_{p}", "1", 8)
        c.add(f"if self.prom_{n}_0 + self.prom_{n}_1 + self.prom_{n}_2 > 1:", 7)
        c.add("choice = self.own", 8)
        c.add("if " + " or ".join(f"self.cand_has_{i} != 0" for i in range(LIMIT + 1)) + ":", 8)
        c.add(f"if self.cand_has_{n} == 0:", 9)
        c.error(1, 10)
        c.add("else:", 9)
        c.add("best_count = self.num - self.num", 10)
        c.add(f"best_rank = self.num - self.num + {len(VALUES)}", 10)
        for v in range(1, len(VALUES)):
            c.add(f"if self.count_{n}_{v} > best_count or (self.count_{n}_{v} == best_count and self.count_{n}_{v} != 0 and self.rank_{n}_{v} < best_rank):", 10)
            c.add(f"best_count = self.count_{n}_{v}", 11)
            c.add(f"best_rank = self.rank_{n}_{v}", 11)
            c.add(f"choice = self.num - self.num + {v}", 11)
        c.add("if best_count == 0:", 10)
        c.error(2, 11)
        c.add("if self.status == 0:", 8)
        c.assign(f"pv_has_{n}", "1", 9)
        c.assign(f"pv_{n}", "choice", 9)
        c.send("accept", "-1", "number", "choice", indent=9)
    c.add("elif event == 13:", 4)
    c.assign("num", "max(self.num, number)", 5)
    for n in range(LIMIT + 1):
        c.add(f"if number == {n}:", 5)
        c.assign(f"acc_has_{n}", "1", 6)
        for p in range(3):
            c.add(f"if sender == {p}:", 6)
            c.assign(f"acc_{n}_{p}", "1", 7)
        c.add(f"if self.acc_{n}_0 + self.acc_{n}_1 + self.acc_{n}_2 > 1 and self.accepted == 0:", 6)
        c.add(f"if self.pv_has_{n} == 0:", 7)
        c.error(1, 8)
        c.add("else:", 7)
        # The print's value and the stored value need not agree: preserve both.
        c.assign("declared", "1", 8)
        c.assign("declared_num", "number", 8)
        c.assign("declared_value", f"self.pv_{n}", 8)
        c.assign("accepted", "value", 8)
    # Bound checks are an explicit modelling outcome, not source exceptions.
    c.add(f"if self.num > {LIMIT} or self.out_num > {LIMIT} or number > {LIMIT}:", 2)
    c.assign("status", "2", 3)
    c.add(f"if value < 0 or value >= {len(VALUES)} or prior_value < 0 or prior_value >= {len(VALUES)} or sender < 0 or sender >= 3:", 2)
    c.assign("status", "2", 3)
    for n in range(LIMIT + 1):
        c.add("if " + " or ".join(f"self.count_{n}_{v} > {CONFIG['max_count']}" for v in range(1, len(VALUES))) + ":", 2)
        c.assign("status", "2", 3)
    c.add("return 0", 2)
    output = ROOT / "generated"
    output.mkdir(exist_ok=True)
    (output / "node.py").write_text("\n".join(c.lines) + "\n")
    manifest = dict(CONFIG, inputs=INPUTS, initial=schema, kinds=KINDS,
                    source_map={"propose": [31, 47], "early_reject": [57, 60],
                                "prepare": [65, 79], "accept": [82, 94],
                                "promise": [95, 120], "accepted": [122, 129], "tick": [141, 157]},
                    pc={"0": "idle", "1": "return after send", "2": "increment num after propose send", "3": "two increments after tick/propose send"},
                    status={"0": "running", "1": "source exception", "2": "out of scope"},
                    fault={"1": "KeyError", "2": "IndexError"})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Generated {len(schema)} scalar state fields; source hash {actual}")


if __name__ == "__main__":
    generate()
