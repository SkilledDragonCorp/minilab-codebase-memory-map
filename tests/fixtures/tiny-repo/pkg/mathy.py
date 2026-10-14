"""Second fixture module so the graph has more than one file node."""


def add(a: int, b: int) -> int:
    return a + b


def greet_sum(a: int, b: int) -> str:
    from src.hello import greet

    return greet(str(add(a, b)))
