"""Executable examples with different schemas and control flow; no custom lowering."""
from rmverify import Specification, Contract, Call, Trace


class Transfer:
    left: int
    right: int

    def __init__(self) -> None:
        self.left = 10
        self.right = 0

    def move(self, amount: int) -> int:
        if amount < 0 or amount > self.left:
            return 0
        self.left -= amount
        self.right += amount
        return amount


def conserved(state: Transfer) -> bool:
    return state.left + state.right == 10


def balances(state: Transfer) -> bool:
    return state.left >= 0 and state.right >= 0


def available(before: Transfer, amount: int) -> bool:
    return 0 <= amount and amount <= before.left


def transferred(before: Transfer, after: Transfer, result: int, amount: int) -> bool:
    return result == amount and after.left == before.left - amount and after.right == before.right + amount


transfer = Specification(Transfer,[Transfer.move],invariants=[conserved,balances],
    contracts={Transfer.move:Contract(requires=available,ensures=transferred)},
    checks=[Trace([Call("move",amount=4),Call("move",amount=100),Call("move",amount=-5)])])


class Register:
    value: int
    enabled: bool

    def __init__(self) -> None:
        self.value = 0
        self.enabled = False

    def enable(self, enabled: bool) -> None:
        self.enabled = enabled

    def write(self, value: int) -> bool:
        if not self.enabled:
            return False
        value = max(value, 0)
        self.value = value
        return True


def nonnegative(state: Register) -> bool:
    return state.value >= 0


def write_result(before: Register, after: Register, result: bool, value: int) -> bool:
    return result == before.enabled and (not result or after.value == max(value, 0))


register = Specification(Register,[Register.enable,Register.write],invariants=[nonnegative],
    contracts={Register.write:Contract(ensures=write_result)},
    checks=[Trace([Call("write",value=-7),Call("enable",enabled=True),Call("write",value=42)])])


class Renamed:
    tally: int
    marker: int

    def __init__(self) -> None:
        self.tally: int = 0
        self.marker: int = 0

    def accept(self, tally: int) -> int:
        marker: int = self.tally
        self.tally = max(tally, self.tally)
        self.marker = marker
        return self.tally - self.marker


def ordered(state: Renamed) -> bool:
    return state.tally >= state.marker and state.marker >= 0


def difference(before: Renamed, after: Renamed, result: int, tally: int) -> bool:
    return result == after.tally - before.tally and result >= 0


renamed = Specification(Renamed,[Renamed.accept],invariants=[ordered],
    contracts={Renamed.accept:Contract(ensures=difference)},
    checks=[Trace([Call("accept",tally=-5),Call("accept",tally=9),Call("accept",tally=4)])])


class NeedsStrengthening:
    x: int
    y: int

    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def tick(self) -> None:
        self.x = self.y


def x_nonnegative(state: NeedsStrengthening) -> bool:
    return state.x >= 0


def y_nonnegative(state: NeedsStrengthening) -> bool:
    return state.y >= 0


unstrengthened = Specification(NeedsStrengthening,[NeedsStrengthening.tick],invariants=[x_nonnegative])
strengthened = Specification(NeedsStrengthening,[NeedsStrengthening.tick],invariants=[x_nonnegative],strengthening=[y_nonnegative])


class Broken:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def offer(self, amount: int) -> int:
        self.value = amount
        return amount


def broken_nonnegative(state: Broken) -> bool:
    return state.value >= 0


def positive(before: Broken, amount: int) -> bool:
    return amount >= 0


def positive_result(before: Broken, after: Broken, result: int, amount: int) -> bool:
    return after.value >= 0 and result >= 0


def wrong_result(before: Broken, after: Broken, result: int, amount: int) -> bool:
    return result > amount


broken = Specification(Broken,[Broken.offer],invariants=[broken_nonnegative],
    contracts={Broken.offer:Contract(requires=positive,ensures=positive_result)})
broken_contract = Specification(Broken,[Broken.offer],contracts={Broken.offer:Contract(ensures=wrong_result)})
