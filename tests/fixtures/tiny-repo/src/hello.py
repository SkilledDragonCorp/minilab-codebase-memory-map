"""Tiny fixture module for local graph indexing."""


def greet(name: str) -> str:
    return f"hello, {name}"


def main() -> None:
    print(greet("skilleddragon"))


if __name__ == "__main__":
    main()
