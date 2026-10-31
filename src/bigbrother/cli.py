import argparse

from bigbrother import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bigbrother",
        description="Check the claims in an issue or pull request against the code.",
    )
    parser.add_argument("--version", action="version", version=f"bigbrother {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0
