#!/usr/bin/env python3

import sys


def usage() -> None:
    print(f"{sys.argv[0]} <wiki src dir> <markdown dest dir>")


def main(wiki_src: str, markdown_dest: str) -> None:
    print(f"wiki-sync'ing from {wiki_src} to {markdown_dest}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
        exit(1)

    main(sys.argv[1], sys.argv[2])
