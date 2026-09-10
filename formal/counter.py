"""Executable counter; these exact methods are compiled to reactive modules."""


class Counter:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def step(self, offered: int) -> None:
        if offered > self.value:
            self.value = offered


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=int, nargs="*")
    counter = Counter()
    for offered in parser.parse_args().inputs:
        counter.step(offered)
        print(counter.value)
